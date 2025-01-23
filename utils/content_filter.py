"""Content filtering utility using Claude API with persistent memory"""
import os
import json
from typing import List, Dict, Any, Optional
import logging
from dotenv import load_dotenv
from datetime import datetime, timedelta
import re
from tenacity import retry, stop_after_attempt, wait_exponential
import sqlite3
from pathlib import Path
import hashlib
import traceback
import httpx
from anthropic import Anthropic

load_dotenv()
logger = logging.getLogger(__name__)

class ContentFilter:
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
            
        self.historical_content = {
            'source_records': {},     # Record historical content per source
            'processed_items': [],    # Record processed premium content
            'selection_history': []   # Record selection decision history
        }
        self._init_database()
        
        # 使用自定义的 httpx 客户端初始化
        http_client = httpx.Client(
            base_url="https://api.anthropic.com",
            headers={"anthropic-version": "2023-06-01"},
            timeout=30.0
        )
        self.client = Anthropic(
            api_key=self.api_key,
            http_client=http_client
        )

    def _init_database(self):
        """Initialize enhanced SQLite database for persistent storage"""
        db_path = Path(os.path.dirname(__file__)) / "content_history.db"
        self.db_path = db_path
        
        with sqlite3.connect(str(db_path)) as conn:
            c = conn.cursor()
            
            try:
                # Drop existing tables if they exist
                c.execute("DROP TABLE IF EXISTS content_history")
                c.execute("DROP TABLE IF EXISTS selection_patterns")
                c.execute("DROP TABLE IF EXISTS content_correlations")
                c.execute("DROP TABLE IF EXISTS selection_audit")
                
                # Enhanced content history table
                c.execute('''CREATE TABLE IF NOT EXISTS content_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_source TEXT,
                    original_title TEXT,
                    original_url TEXT UNIQUE,
                    content_text TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    content_hash TEXT UNIQUE,
                    engagement_score REAL DEFAULT 0,
                    persistence_score REAL DEFAULT 0,
                    selection_count INTEGER DEFAULT 0,
                    last_referenced DATETIME,
                    correlation_score REAL DEFAULT 0
                )''')
                
                # Enhanced selection patterns table
                c.execute('''CREATE TABLE IF NOT EXISTS selection_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT,
                    pattern_value TEXT,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    avg_engagement REAL DEFAULT 0,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )''')
                
                # New cross-reference table
                c.execute('''CREATE TABLE IF NOT EXISTS content_correlations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_url TEXT,
                    target_url TEXT,
                    correlation_type TEXT,
                    correlation_strength REAL DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(source_url, target_url)
                )''')
                
                # New content audit table
                c.execute('''CREATE TABLE IF NOT EXISTS selection_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    selection_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    content_url TEXT,
                    selection_reason TEXT,
                    score_breakdown TEXT,
                    historical_context TEXT,
                    pattern_matches TEXT
                )''')
                
                conn.commit()
                logger.info("数据库表初始化成功")
                
            except sqlite3.Error as e:
                logger.error(f"数据库初始化失败: {str(e)}")
                raise

    def filter_content(self, content_items: Dict[str, List[Dict[str, Any]]] | List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        try:
            # 输入预处理
            if isinstance(content_items, dict):
                flattened_items = []
                for source, items in content_items.items():
                    if not isinstance(items, list):
                        logger.error(f"来源 {source} 的内容不是列表: {type(items)}")
                        continue
                    for item in items:
                        if isinstance(item, dict):
                            if 'source' not in item:
                                item['source'] = source
                            flattened_items.append(item)
                content_items = flattened_items
                logger.info(f"将字典格式转换为列表格式，共 {len(content_items)} 条新闻")
            
            if not isinstance(content_items, list):
                logger.error(f"输入类型错误: 期望 list，实际是 {type(content_items)}")
                return []
                
            logger.info(f"收到 {len(content_items)} 条新闻")
            
            # 按来源分组统计
            sources_count = {}
            for item in content_items:
                source = item.get('source', 'unknown')
                if source not in sources_count:
                    sources_count[source] = 0
                sources_count[source] += 1
            logger.info(f"新闻来源统计: {json.dumps(sources_count, ensure_ascii=False)}")
            
            prompt = f"""分析以下新闻内容，并选择最有价值的内容。仅返回JSON数组，不要返回任何其他内容。

当前共有 {len(content_items)} 条新闻，来自以下来源：
{json.dumps(sources_count, ensure_ascii=False, indent=2)}

新闻内容：
{json.dumps(content_items, ensure_ascii=False, indent=2)}

选择标准：
1. 新闻的重要性和影响力（40%）
2. 新闻的时效性（20%）
3. 新闻的可信度（20%）
4. 新闻的实用价值（20%）

严格要求：
1. 只返回一个JSON数组，不要包含任何其他内容（如代码块标记、说明文字等）
2. JSON数组中的每个对象必须且只能包含以下字段：
   - source: 新闻来源（与原文完全一致）
   - title: 新闻标题（与原文完全一致）
   - url: 新闻链接（与原文完全一致）
   - value_summary: 新闻价值总结（限100字内）
3. 所有字符串必须使用双引号
4. 每个来源至少选择一条最有价值的新闻
5. 总数控制在3-5条之间
6. 不得添加任何额外字段
7. 不得修改原文中的任何内容"""

            logger.debug(f"发送到 Claude 的提示词:\n{prompt}")
            
            # 调用 Claude API
            response = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=2000,
                temperature=0.3,
                system="你是一个新闻价值评估专家。你需要仅返回JSON格式的筛选结果，不要返回任何其他内容。",
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            try:
                content = response.content[0].text
                logger.debug(f"Claude 原始响应:\n{content}")
                
                content = content.strip()
                if '```' in content:
                    for line in content.split('\n'):
                        line = line.strip()
                        if line.startswith('[') and line.endswith(']'):
                            content = line
                            break
                        try:
                            test_json = json.loads(line)
                            if isinstance(test_json, list):
                                content = line
                                break
                        except:
                            continue
                
                logger.debug(f"预处理后的JSON内容:\n{content}")
                
                try:
                    filtered_content = json.loads(content)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON解析错误: {str(e)}")
                    logger.error(f"问题字符附近的内容: {content[max(0, e.pos-50):min(len(content), e.pos+50)]}")
                    logger.error(f"错误位置: 第{e.lineno}行，第{e.colno}列，字符位置{e.pos}")
                    return []
                
                if not isinstance(filtered_content, list):
                    logger.error(f"返回内容不是数组: {type(filtered_content)}")
                    return []
                
                # 验证结果
                valid_content = []
                selected_sources = set()
                
                for item in filtered_content:
                    if not isinstance(item, dict):
                        logger.warning(f"跳过非字典项: {item}")
                        continue
                        
                    required_fields = {'source', 'title', 'url', 'value_summary'}
                    if not all(k in item for k in required_fields):
                        missing = required_fields - set(item.keys())
                        logger.warning(f"跳过缺少字段的项: {missing}")
                        continue
                    
                    # 验证与原文匹配
                    matched = False
                    for original in content_items:
                        if (item['source'] == original.get('source', '') and
                            item['title'] == original.get('title', '') and
                            item['url'] == original.get('url', '')):
                            matched = True
                            break
                    
                    if not matched:
                        logger.warning(f"跳过不匹配项: {item}")
                        continue
                    
                    valid_content.append(item)
                    selected_sources.add(item['source'])
                
                logger.info(f"筛选完成: 保留 {len(valid_content)}/{len(filtered_content)} 条内容")
                logger.info(f"已选择的来源: {sorted(list(selected_sources))}")
                return valid_content
                
            except Exception as e:
                logger.error(f"处理响应时出错: {str(e)}")
                logger.debug(traceback.format_exc())
                return []
                
        except Exception as e:
            logger.error(f"内容筛选失败: {str(e)}")
            logger.debug(traceback.format_exc())
            return []

    def _compute_content_hash(self, item: Dict[str, Any]) -> str:
        content_str = (
            f"{item.get('original_title', '')}"
            f"{item.get('original_url', '')}"
            f"{item.get('description', '')}"
        )
        return hashlib.sha256(content_str.encode()).hexdigest()

    def _store_content(self, item: Dict[str, Any], engagement_score: float = 0.8, 
                      persistence_score: float = 0.7, correlation_score: float = 0.6):
        content_hash = self._compute_content_hash(item)
        
        with sqlite3.connect(str(self.db_path)) as conn:
            c = conn.cursor()
            try:
                c.execute('''INSERT OR REPLACE INTO content_history 
                    (original_source, original_title, original_url, content_text,
                     content_hash, engagement_score, persistence_score, correlation_score,
                     last_referenced)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)''',
                    (item.get('source'), item.get('title'),
                     item.get('url'), item.get('value_summary', ''),
                     content_hash, engagement_score, persistence_score, correlation_score))
                conn.commit()
            except sqlite3.Error as e:
                logger.error(f"Database error in _store_content: {str(e)}")
                raise