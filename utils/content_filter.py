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

load_dotenv()
logger = logging.getLogger(__name__)

class ContentFilter:
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.historical_content = {
            'source_records': {},     # Record historical content per source
            'processed_items': [],    # Record processed premium content
            'selection_history': []   # Record selection decision history
        }
        self._init_database()
        self.PROMPT_TEMPLATE = """Analyze and select the most valuable content considering ALL historical and current sources:

1. Return EXACTLY 5 items total
2. Include content from ALL available sources
3. Evaluate based on:
   - Technical depth and insights
   - Practical value and applicability
   - Current relevance and impact
   - Source reliability and authority
   - Historical context and trends
   - Cross-source correlations
   - User engagement patterns
   - Content persistence value

Current content to analyze: %s
Historical context: %s
Selection patterns: %s

Return ONLY a JSON array with exactly 5 items. Each item must include:
- original_source
- original_title 
- original_url
- value_summary (max 100 chars)
- selection_reason (brief explanation of cross-source value and historical significance)
- cross_references (array of related content URLs)"""

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

    def _compute_content_hash(self, item: Dict[str, Any]) -> str:
        """Generate improved unique hash for content deduplication"""
        content_str = (
            f"{item.get('original_title', '')}"
            f"{item.get('original_url', '')}"
            f"{item.get('description', '')}"
        )
        return hashlib.sha256(content_str.encode()).hexdigest()

    def _store_content(self, item: Dict[str, Any], engagement_score: float, 
                      persistence_score: float = 0, correlation_score: float = 0):
        """Store enhanced content data with additional metrics"""
        content_hash = self._compute_content_hash(item)
        
        with sqlite3.connect(str(self.db_path)) as conn:
            c = conn.cursor()
            try:
                c.execute('''INSERT OR REPLACE INTO content_history 
                    (original_source, original_title, original_url, content_text,
                     content_hash, engagement_score, persistence_score, correlation_score,
                     last_referenced)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)''',
                    (item.get('original_source'), item.get('original_title'),
                     item.get('original_url'), item.get('description', ''),
                     content_hash, engagement_score, persistence_score, correlation_score))
                conn.commit()
            except sqlite3.Error as e:
                logger.error(f"Database error in _store_content: {str(e)}")
                raise

    def _get_historical_context(self, lookback_days: int = 30) -> Dict[str, Any]:
        """Retrieve comprehensive historical context for intelligent selection"""
        with sqlite3.connect(str(self.db_path)) as conn:
            c = conn.cursor()
            
            try:
                # Get successful patterns
                c.execute('''SELECT pattern_type, pattern_value, success_count, 
                            avg_engagement 
                    FROM selection_patterns 
                    WHERE success_count > 0
                    ORDER BY success_count DESC LIMIT 15''')
                patterns = c.fetchall()
                
                # Get high-value historical content
                period_ago = datetime.now() - timedelta(days=lookback_days)
                c.execute('''SELECT original_source, original_url, engagement_score,
                            persistence_score, correlation_score
                    FROM content_history 
                    WHERE timestamp > ? 
                    ORDER BY (engagement_score + persistence_score + correlation_score) DESC 
                    LIMIT 20''',
                    (period_ago,))
                historical_content = c.fetchall()
                
                # Get significant correlations
                c.execute('''SELECT source_url, target_url, correlation_type, 
                            correlation_strength
                    FROM content_correlations
                    WHERE correlation_strength > 0.7
                    ORDER BY correlation_strength DESC
                    LIMIT 10''')
                correlations = c.fetchall()
                
                return {
                    "successful_patterns": patterns,
                    "historical_highlights": historical_content,
                    "content_correlations": correlations,
                    "timespan": f"Past {lookback_days} days"
                }
            except sqlite3.Error as e:
                logger.error(f"Database error in _get_historical_context: {str(e)}")
                return {
                    "successful_patterns": [],
                    "historical_highlights": [],
                    "content_correlations": [],
                    "timespan": f"Past {lookback_days} days"
                }

    def filter_content(self, content_items: Dict[str, List[Dict[str, Any]]] | List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        使用 Claude API 智能筛选内容
        
        Args:
            content_items: 要筛选的内容，可以是字典或列表
                如果是字典，格式应该是 {"source1": [items], "source2": [items]}
                如果是列表，格式应该是 [{"source": "source1", ...}, {"source": "source2", ...}]
        
        Returns:
            List[Dict]: 筛选后的内容列表
        """
        try:
            # 输入预处理
            if isinstance(content_items, dict):
                # 将字典格式转换为列表格式
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
            logger.debug(f"输入内容: {json.dumps(content_items, ensure_ascii=False, indent=2)}")
            
            # 按来源分组统计
            sources_count = {}
            for item in content_items:
                source = item.get('source', 'unknown')
                if source not in sources_count:
                    sources_count[source] = 0
                sources_count[source] += 1
            logger.info(f"新闻来源统计: {json.dumps(sources_count, ensure_ascii=False)}")
            
            # 获取历史上下文
            historical_context = self._get_historical_context()
            
            # 构建完整提示词
            prompt = f"""请分析以下新闻内容，并选择最有价值的内容。

当前共有 {len(content_items)} 条新闻，来自以下来源：
{json.dumps(sources_count, ensure_ascii=False, indent=2)}

新闻内容：
{json.dumps(content_items, ensure_ascii=False, indent=2)}

请从以下几个方面进行分析：
1. 新闻的重要性和影响力（占比40%）
2. 新闻的时效性（占比20%）
3. 新闻的可信度（占比20%）
4. 新闻的实用价值（占比20%）

请返回一个 JSON 数组，数组中的每个元素应该包含以下字段：
- source: 新闻来源（必须与原文的source字段完全一致）
- title: 新闻标题（必须与原文的title字段完全一致）
- url: 新闻链接（必须与原文的url字段完全一致）
- value_summary: 新闻价值总结（不超过100字）

要求：
1. 只返回 JSON 数组，不要包含其他文字
2. 确保 JSON 格式正确，所有字符串都要用双引号
3. 从每个来源至少选择一条最有价值的新闻
4. 如果某个来源的新闻都不够价值，可以不选
5. 总共选择3-5条最有价值的新闻
6. 字段值必须与原文完全一致，不要修改或重写
"""
            logger.debug(f"发送到 Claude 的提示词:\n{prompt}")
            
            # 调用 Claude API
            from anthropic import Anthropic
            client = Anthropic(api_key=self.api_key)
            
            response = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=2000,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # 解析响应
            try:
                # 获取最后一条消息的内容
                content = response.content[0].text
                logger.debug(f"Claude 原始响应: {content}")
                
                # 尝试提取 JSON 部分
                content = content.strip()
                if content.startswith('```json'):
                    content = content[7:]
                if content.endswith('```'):
                    content = content[:-3]
                content = content.strip()
                
                filtered_content = json.loads(content)
                if not isinstance(filtered_content, list):
                    logger.error("Claude 返回的不是数组格式")
                    return []
                    
                # 验证每个项目的格式和内容
                valid_content = []
                selected_sources = set()
                
                for item in filtered_content:
                    if not isinstance(item, dict):
                        logger.warning(f"跳过非字典项: {item}")
                        continue
                        
                    if not all(k in item for k in ['source', 'title', 'url', 'value_summary']):
                        logger.warning(f"跳过缺少必要字段的项: {item}")
                        continue
                        
                    # 验证source、title和url是否与原文匹配
                    source_match = False
                    for original_item in content_items:
                        if (item['source'] == original_item.get('source') and
                            item['title'] == original_item.get('title') and
                            item['url'] == original_item.get('url')):
                            source_match = True
                            break
                    
                    if not source_match:
                        logger.warning(f"跳过与原文不匹配的项: {item}")
                        continue
                        
                    valid_content.append(item)
                    selected_sources.add(item['source'])
                
                logger.info(f"筛选结果: 保留 {len(valid_content)}/{len(content_items)} 条新闻")
                logger.info(f"已选择的来源: {selected_sources}")
                logger.debug(f"筛选后的内容: {json.dumps(valid_content, ensure_ascii=False, indent=2)}")
                
                # 更新选择历史
                self.historical_content['selection_history'].append({
                    'timestamp': datetime.now().isoformat(),
                    'selected_items': [item['url'] for item in valid_content]
                })
                
                # 存储筛选后的内容
                for item in valid_content:
                    self._store_content(
                        item,
                        engagement_score=0.8,
                        persistence_score=0.7,
                        correlation_score=0.6
                    )
                
                return valid_content
                
            except json.JSONDecodeError as e:
                logger.error(f"解析 Claude 响应失败: {str(e)}")
                logger.debug(f"问题响应内容: {content}")
                return []
            except Exception as e:
                logger.error(f"处理 Claude 响应时发生错误: {str(e)}")
                logger.debug(traceback.format_exc())
                return []
                
        except Exception as e:
            logger.error(f"内容筛选失败: {str(e)}")
            logger.debug(traceback.format_exc())
            return []
            
    def _update_selection_patterns(self, selected_items: List[Dict[str, Any]]):
        """更新选择模式统计"""
        with sqlite3.connect(str(self.db_path)) as conn:
            c = conn.cursor()
            for item in selected_items:
                # 更新源统计
                c.execute('''INSERT OR REPLACE INTO selection_patterns 
                    (pattern_type, pattern_value, success_count, last_updated)
                    VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT(pattern_type, pattern_value) 
                    DO UPDATE SET success_count = success_count + 1,
                    last_updated = CURRENT_TIMESTAMP''',
                    ('source', item['original_source']))
                
                # 可以添加更多模式统计，如主题、关键词等
                
            conn.commit()