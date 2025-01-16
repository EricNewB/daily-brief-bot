import requests

class BraveSearch:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = 'https://api.search.brave.com/v1'
        self.headers = {
            'Accept': 'application/json',
            'X-Brave-API-Key': api_key
        }
    
    def search(self, query, count=5):
        """Search news using Brave Search API"""
        params = {
            'q': query,
            'count': count,
            'type': 'news',     # 指定搜索新闻
            'freshness': 'day'  # 只获取最近的新闻
        }
        
        try:
            response = requests.get(
                self.base_url,
                headers=self.headers,
                params=params
            )
    # 添加调试信息
    print(f'Request URL: {response.url}')
    print(f'Request headers: {self.headers}')
    
    response.raise_for_status()
    data = response.json()
    
    # 提取新闻内容
    if 'news' in data:
        return data['news']
    elif 'webPages' in data:  # 如果没有新闻，回退到网页结果
        return data['webPages']['value']
    return []
    
except requests.RequestException as e:
    print(f'Error in Brave Search: {e}')
    if hasattr(e.response, 'text'):
        print(f'Response content: {e.response.text}')
    return []
