"""Content filtering utility"""
import os
import json
import logging
import re
import httpx
from anthropic import Anthropic
from pathlib import Path

logger = logging.getLogger(__name__)

class BaseContentFilter:
    """基础内容过滤器"""
    def filter_content(self, content_items):
        raise NotImplementedError

class AIContentFilter(BaseContentFilter):
    """AI内容过滤器"""
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
        
        http_client = httpx.Client(
            base_url="https://api.anthropic.com",
            headers={"anthropic-version": "2023-06-01"},
            timeout=30.0
        )
        self.client = Anthropic(
            api_key=self.api_key,
            http_client=http_client
        )

    def filter_content(self, content_items):
        try:
            # 输入预处理
            if isinstance(content_items, dict):
                items = []
                for source, source_items in content_items.items():
                    if isinstance(source_items, list):
                        for item in source_items:
                            if isinstance(item, dict):
                                item['source'] = source
                                items.append(item)
                content_items = items
            
            logger.info(f"AI开始筛选 {len(content_items)} 条内容")
            
            # 直接使用所有内容，暂时不做AI筛选
            filtered_items = content_items
            
            # 为每个内容添加评论
            for item in filtered_items:
                if 'title' in item:
                    item['comment'] = self._generate_comment(item['title'])
                    
            return filtered_items
            
        except Exception as e:
            logger.error(f"AI筛选失败: {str(e)}")
            return []

    def _build_prompt(self, content_items):
        sources_count = {}
        for item in content_items:
            source = item.get('source', 'unknown')
            sources_count[source] = sources_count.get(source, 0) + 1

        return f"""分析以下新闻内容，并选择最有价值的内容。仅返回JSON数组，不要返回任何其他内容。

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
1. 只返回一个JSON数组，不要包含任何其他内容
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

    def _parse_response(self, content):
        try:
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
            
            return json.loads(content)
        except Exception as e:
            logger.error(f"解析AI响应失败: {str(e)}")
            return []

    def _generate_comment(self, title):
        try:
            response = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=50,
                temperature=0.9,
                messages=[{
                    "role": "user",
                    "content": f"请用一句话点评这条新闻（不超过20字，不要标点符号）：{title}"
                }]
            )
            comment = response.content[0].text.strip()
            comment = re.sub(r'[^\w\s]', '', comment)  # 移除标点符号
            if len(comment) > 20:
                comment = comment[:20]
            logger.info(f"生成点评: {comment}")
            return comment
        except Exception as e:
            logger.error(f"生成评论失败: {str(e)}")
            return ""

class RuleContentFilter(BaseContentFilter):
    """规则内容过滤器"""
    def __init__(self):
        self.keywords = self._load_keywords()
        self.categories = {
            'academic': {
                'name': '学术科技',
                'keywords': ['tech', 'ai', 'programming', 'software', 'algorithm',
                           '技术', '编程', '人工智能', '算法', '开发']
            },
            'gaming': {
                'name': '游戏资讯',
                'keywords': ['game', 'gaming', 'steam', 'xbox', 'playstation', 'nintendo',
                           '游戏', '手游', '主机']
            },
            'china_news': {
                'name': '国内新闻',
                'keywords': ['china', 'chinese', 'beijing', 'shanghai',
                           '中国', '国内', '北京', '上海', '政策', '改革']
            },
            'international_news': {
                'name': '国际新闻',
                'keywords': []  # 默认分类
            }
        }
    
    def _load_keywords(self):
        try:
            with open('config/keywords.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            default_keywords = {
                'include': ['技术', '编程', '开发', 'AI', '人工智能', '科技'],
                'exclude': ['广告', '推广', '抽奖', '红包']
            }
            os.makedirs('config', exist_ok=True)
            with open('config/keywords.json', 'w', encoding='utf-8') as f:
                json.dump(default_keywords, f, ensure_ascii=False, indent=2)
            return default_keywords
    
    def filter_content(self, content_items):
        filtered_content = []
        
        # 转换输入格式
        if isinstance(content_items, dict):
            items = []
            for source, source_items in content_items.items():
                if isinstance(source_items, list):
                    for item in source_items:
                        if isinstance(item, dict):
                            item['source'] = source
                            items.append(item)
            content_items = items
        
        logger.info(f"开始筛选 {len(content_items)} 条内容")
        
        for item in content_items:
            title = item.get('title', '').lower()
            desc = item.get('description', '').lower() if item.get('description') else ''
            source = item.get('source', '').lower()
            
            # 直接添加所有内容，暂时不做筛选
            filtered_content.append(item)
            logger.info(f"添加内容: {title} (来源: {source})")
        
        return filtered_content

    def categorize_content(self, filtered_items):
        """将筛选后的内容分类到不同板块"""
        categorized = {cat: [] for cat in self.categories}
        
        for item in filtered_items:
            title = item.get('title', '').lower()
            desc = item.get('description', '').lower() if item.get('description') else ''
            source = item.get('source', '').lower()
            content_text = f"{title} {desc}"
            
            # 根据来源预分类
            if source == 'weibo':
                categorized['china_news'].append(item)
                continue
            elif source == 'bilibili':
                categorized['gaming'].append(item)
                continue
            elif source == 'hackernews':
                categorized['academic'].append(item)
                continue
            
            # 根据关键词分类
            has_categorized = False  # 修改变量名避免冲突
            for cat, info in self.categories.items():
                if info['keywords'] and any(kw in content_text for kw in info['keywords']):
                    categorized[cat].append(item)
                    has_categorized = True
                    break
            
            # 未分类的内容归入国际新闻
            if not has_categorized:
                categorized['international_news'].append(item)
        
        return categorized

def create_content_filter():
    """工厂函数，根据配置创建对应的过滤器"""
    try:
        with open('config/filter_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            mode = config.get('mode', 'rule')
    except FileNotFoundError:
        mode = 'rule'
    
    if mode == 'ai':
        return AIContentFilter()
    else:
        return RuleContentFilter()

class ContentFilterManager:
    def __init__(self):
        self.filter = create_content_filter()
    
    def filter_content(self, content_items):
        return self.filter.filter_content(content_items)
    
    def categorize_content(self, filtered_items):
        """将筛选后的内容分类到不同板块"""
        if isinstance(self.filter, RuleContentFilter):
            return self.filter.categorize_content(filtered_items)
        
        # 如果是 AI 过滤器，使用默认分类
        categorized = {
            'academic': [],
            'international_news': [],
            'gaming': [],
            'china_news': []
        }
        
        # 简单分类逻辑
        for item in filtered_items:
            source = item.get('source', '').lower()
            if source == 'weibo':
                categorized['china_news'].append(item)
            elif source == 'bilibili':
                categorized['gaming'].append(item)
            elif source == 'hackernews':
                categorized['academic'].append(item)
            else:
                categorized['international_news'].append(item)
        
        return categorized
    
    @property
    def categories(self):
        """获取分类信息"""
        if isinstance(self.filter, RuleContentFilter):
            return self.filter.categories
        else:
            # 返回默认分类信息
            return {
                'academic': {'name': '学术科技'},
                'international_news': {'name': '国际新闻'},
                'gaming': {'name': '游戏资讯'},
                'china_news': {'name': '国内新闻'}
            }