"""
Weibo hot search crawler with enhanced error handling
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import traceback
import json

class WeiboCrawler:
    def __init__(self):
        self.api_url = "https://m.weibo.cn/api/container/getIndex?containerid=106003type%3D25%26t%3D3%26disable_hot%3D1%26filter_type%3Drealtimehot"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://weibo.com/',
            'Origin': 'https://weibo.com',
            'Connection': 'keep-alive'
        }
        
    def fetch_trending(self, limit=5):
        """Fetch hot topics from Weibo"""
        try:
            print(f"Fetching hot topics from Weibo API")
            response = requests.get(
                self.api_url, 
                headers=self.headers, 
                timeout=10
            )
            response.raise_for_status()
            
            print(f"Response status: {response.status_code}")
            print(f"Response encoding: {response.encoding}")
            
            # Parse JSON response
            data = response.json()
            if 'data' not in data or 'cards' not in data['data'] or len(data['data']['cards']) == 0:
                print("Invalid response format")
                print(f"Response data: {json.dumps(data, ensure_ascii=False, indent=2)}")
                return []
            
            topics = []
            card_group = data['data']['cards'][0].get('card_group', [])
            print(f"Found {len(card_group)} topics")
            
            for idx, topic in enumerate(card_group[:limit], 1):
                try:
                    # Skip non-topic cards
                    if topic.get('card_type') != 4:
                        continue
                        
                    # Extract topic details
                    desc = topic.get('desc', '')
                    scheme = topic.get('scheme', '')
                    hot_value = topic.get('desc_extr', 0)
                    
                    if isinstance(hot_value, str):
                        if hot_value == '正在热转':
                            hot_value = 0
                        else:
                            hot_value = int(''.join(filter(str.isdigit, hot_value)))
                    
                    topic_info = {
                        'title': desc,
                        'url': scheme,
                        'hot_value': hot_value,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'source': 'Weibo'
                    }
                    topics.append(topic_info)
                    print(f"Added topic {idx}: {topic_info['title']} ({topic_info['hot_value']})")
                    
                    if len(topics) >= limit:
                        break
                    
                except Exception as e:
                    print(f"Error processing topic {idx}: {str(e)}")
                    continue
            
            print(f"Successfully fetched {len(topics)} topics")
            return topics
            
        except requests.RequestException as e:
            print(f"Network error fetching Weibo topics: {str(e)}")
            print(f"Headers: {self.headers}")
            return []
        except Exception as e:
            print(f"Error fetching Weibo topics: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return []