"""
Xiaohongshu trending topics crawler (Web Search Version)
"""
import requests
from datetime import datetime
import random
import time
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import urlencode

class XiaohongshuCrawler:
    def __init__(self):
        self.search_url = "https://www.xiaohongshu.com/search_result"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        })
        
    def get_search_results(self, keyword, limit=5):
        """获取搜索结果"""
        try:
            params = {
                'keyword': keyword,
                'sort': 'general',
                'page': 1,
                'page_size': limit
            }
            
            search_url = f"{self.search_url}?{urlencode(params)}"
            print(f"请求URL: {search_url}")
            
            response = self.session.get(search_url, timeout=10)
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                # 提取script标签中的初始数据
                pattern = r'window\.__INITIAL_STATE__\s*=\s*({[^<]+});?'
                match = re.search(pattern, response.text)
                
                if match:
                    data = json.loads(match.group(1))
                    return data.get('searchResult', {}).get('items', [])
            return []
            
        except Exception as e:
            print(f"获取搜索结果出错: {str(e)}")
            return []
    
    def fetch_trending(self, limit=5):
        """获取热门内容"""
        try:
            print("开始获取小红书热门...")
            
            # 随机休眠
            delay = random.uniform(1, 3)
            print(f"等待 {delay:.2f} 秒...")
            time.sleep(delay)
            
            # 使用热门关键词搜索
            keywords = ['穿搭', '美食', '旅行', '护肤', '数码']
            keyword = random.choice(keywords)
            print(f"使用关键词: {keyword}")
            
            items = self.get_search_results(keyword, limit)
            
            if not items:
                print("没有找到相关内容")
                return []
                
            trends = []
            for item in items[:limit]:
                try:
                    note_data = item.get('note', {})
                    if not note_data:
                        continue
                        
                    trend = {
                        'title': note_data.get('title', '').strip() or note_data.get('desc', '').strip(),
                        'url': f"https://www.xiaohongshu.com/discovery/item/{note_data.get('id', '')}",
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'source': 'Xiaohongshu',
                        'keyword': keyword,
                        'likes': note_data.get('interactInfo', {}).get('likedCount', 0)
                    }
                    
                    if not trend['title']:
                        continue
                        
                    print(f"找到内容: {json.dumps(trend, indent=2, ensure_ascii=False)}")
                    trends.append(trend)
                    
                except Exception as e:
                    print(f"处理单条内容时出错: {str(e)}")
                    continue
            
            print(f"成功获取 {len(trends)} 条内容")
            return trends
            
        except Exception as e:
            print(f"获取热门内容出错: {str(e)}")
            return []