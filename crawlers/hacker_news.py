"""
HackerNews crawler with enhanced error handling and debugging
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import traceback
import time
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

logger = logging.getLogger(__name__)

class HackerNewsCrawler:
    def __init__(self):
        self.base_url = "https://news.ycombinator.com/"
        self.api_base_url = "https://hacker-news.firebaseio.com/v0"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # 配置重试策略
        retry_strategy = Retry(
            total=3,  # 最多重试3次
            backoff_factor=1,  # 重试间隔
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        # 创建会话并配置
        self.session = requests.Session()
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self.session.timeout = 30
        
    def fetch_trending(self, limit=5):
        """Fetch top stories from HackerNews with fallback to official API"""
        try:
            # 首先尝试网页抓取
            stories = self._fetch_from_website(limit)
            if stories:
                return stories
                
            # 如果网页抓取失败，使用官方 API
            logger.info("Website scraping failed, falling back to official API")
            return self._fetch_from_api(limit)
            
        except Exception as e:
            logger.error(f"Error fetching HackerNews: {str(e)}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return []
            
    def _fetch_from_website(self, limit):
        """Fetch stories from HackerNews website"""
        try:
            # 添加随机延时
            time.sleep(random.uniform(1, 3))
            
            logger.info(f"Fetching news from {self.base_url}")
            response = self.session.get(self.base_url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            stories = []
            
            items = soup.find_all('tr', class_='athing')
            logger.debug(f"Found {len(items)} stories")
            
            for idx, item in enumerate(items[:limit], 1):
                try:
                    title_link = item.select_one('.titleline > a')
                    if not title_link:
                        logger.warning(f"No title link found in story {idx}")
                        continue
                        
                    subtext = item.find_next_sibling('tr')
                    score = 'No score'
                    if subtext:
                        score_elem = subtext.find('span', class_='score')
                        score = score_elem.text if score_elem else 'No score'
                        
                    story = {
                        'title': title_link.get_text().strip(),
                        'url': title_link.get('href'),
                        'score': score,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'source': 'HackerNews'
                    }
                    stories.append(story)
                    logger.debug(f"Added story {idx}: {story['title']}")
                    
                except Exception as e:
                    logger.error(f"Error processing story {idx}: {str(e)}")
                    continue
                    
            return stories
            
        except Exception as e:
            logger.error(f"Error scraping website: {str(e)}")
            return []
            
    def _fetch_from_api(self, limit):
        """Fetch stories from HackerNews official API"""
        try:
            # 获取热门故事 ID
            top_stories_url = f"{self.api_base_url}/topstories.json"
            response = self.session.get(top_stories_url)
            response.raise_for_status()
            story_ids = response.json()[:limit]
            
            stories = []
            for story_id in story_ids:
                try:
                    # 获取每个故事的详细信息
                    story_url = f"{self.api_base_url}/item/{story_id}.json"
                    story_response = self.session.get(story_url)
                    story_response.raise_for_status()
                    story_data = story_response.json()
                    
                    story = {
                        'title': story_data.get('title', ''),
                        'url': story_data.get('url', ''),
                        'score': f"{story_data.get('score', 0)} points",
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'source': 'HackerNews'
                    }
                    stories.append(story)
                    logger.debug(f"Added story from API: {story['title']}")
                    
                except Exception as e:
                    logger.error(f"Error fetching story {story_id}: {str(e)}")
                    continue
                    
            return stories
            
        except Exception as e:
            logger.error(f"Error fetching from API: {str(e)}")
            return []