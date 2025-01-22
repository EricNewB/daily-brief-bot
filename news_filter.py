"""
Daily Brief News Filter
智能筛选新闻内容的核心功能实现
"""

import json
import asyncio
from typing import List, Dict
import logging
from anthropic import Anthropic
import os
from dotenv import load_dotenv
import traceback

load_dotenv()
logger = logging.getLogger(__name__)

class NewsFilter:
    def __init__(self):
        self.llm_config = {
            "temperature": 0.7,
            "max_tokens": 1000,
            "model": "claude-3-opus-20240229"
        }
        api_key = os.getenv("ANTHROPIC_API_KEY")
        logger.info(f"初始化 NewsFilter，API key 是否存在: {bool(api_key)}")
        self.llm_client = Anthropic(api_key=api_key)
    
    async def filter_news(self, news_items: List[Dict]) -> List[Dict]:
        """
        对新闻列表进行智能筛选
        """
        # 输入验证
        if not isinstance(news_items, list):
            logger.error(f"输入类型错误: 期望 list，实际是 {type(news_items)}")
            return []
            
        logger.info(f"开始处理 {len(news_items)} 条新闻")
        logger.info(f"输入新闻列表: {json.dumps(news_items, ensure_ascii=False, indent=2)}")
        
        filtered_news = []
        
        if not news_items:
            logger.warning("没有接收到任何新闻内容")
            return []
            
        for item in news_items:
            if not isinstance(item, dict):
                logger.error(f"新闻项类型错误: 期望 dict，实际是 {type(item)}")
                continue
                
            source = item.get('source', 'unknown')
            title = item.get('title', '')
            logger.info(f"正在处理来自 {source} 的新闻: {title}")
            
            # 验证必要字段
            if not title or not source:
                logger.warning(f"新闻缺少必要字段: title={bool(title)}, source={bool(source)}")
                continue
                
            try:
                is_valuable = await self._evaluate_news_value(item)
                logger.info(f"新闻评估结果: {title} -> {'保留' if is_valuable else '过滤'}")
                if is_valuable:
                    filtered_news.append(item)
            except Exception as e:
                logger.error(f"处理新闻时发生错误: {str(e)}\n{traceback.format_exc()}")
                filtered_news.append(item)  # 出错时保留新闻
                
        logger.info(f"筛选完成，保留了 {len(filtered_news)}/{len(news_items)} 条新闻")
        logger.info(f"筛选后的新闻列表: {json.dumps(filtered_news, ensure_ascii=False, indent=2)}")
        return filtered_news

    async def _evaluate_news_value(self, news_item: Dict) -> bool:
        """
        评估单条新闻的价值
        """
        title = news_item.get('title', '')
        content = f"{title}\n来源：{news_item.get('source', '')}\n热度：{news_item.get('hot_value', '')}\n{news_item.get('url', '')}"
        logger.debug(f"准备评估新闻:\n{content}")
        try:
            result = await self.evaluate_news(title, content)
            logger.info(f"新闻「{title}」评估结果: {result}")
            return result
        except Exception as e:
            logger.error(f"评估新闻「{title}」时发生错误: {str(e)}")
            return True

    async def evaluate_news(self, title: str, content: str) -> bool:
        """
        评估新闻是否值得保留
        """
        prompt = f"""请分析以下新闻是否值得保留。

标题：{title}
内容：{content}

请从以下几个方面进行分析：
1. 新闻的重要性和影响力
2. 新闻的时效性
3. 新闻的可信度
4. 新闻的实用价值

只需要回答 "true" 表示这是一篇值得保留的新闻，或者 "false" 表示应该过滤掉这篇新闻。
"""
        logger.debug(f"发送到 Claude 的提示词:\n{prompt}")
        
        try:
            response = await asyncio.to_thread(
                self.llm_client.messages.create,
                model=self.llm_config["model"],
                messages=[{"role": "user", "content": prompt}],
                temperature=self.llm_config["temperature"],
                max_tokens=self.llm_config["max_tokens"],
            )
            
            result = response.content[0].text.strip().lower()
            logger.info(f"Claude 对「{title}」的响应: {result}")
            return result == "true"
            
        except Exception as e:
            logger.error(f"调用 Claude API 评估「{title}」时发生错误: {str(e)}\n{traceback.format_exc()}")
            return True  # 发生错误时默认保留该新闻

    async def test_news_sources(self):
        """
        测试各个新闻源的数据收集情况
        """
        sources_stats = {}
        for item in self.news_items:
            source = item.get('source', 'unknown')
            if source not in sources_stats:
                sources_stats[source] = 0
            sources_stats[source] += 1
        
        logger.info("新闻源统计:")
        for source, count in sources_stats.items():
            logger.info(f"{source}: {count} 条新闻")
