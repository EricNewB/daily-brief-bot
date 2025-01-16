import requests
import json
from time import sleep
from typing import List, Dict, Any

class BraveSearch:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.search.brave.com/res/v1/web/search"  # Updated endpoint
        self.headers = {
            'Accept': 'application/json',
            'X-Brave-API-Key': api_key
        }
        self.max_retries = 3
        self.retry_delay = 1  # seconds
    
    def search(self, query: str, count: int = 5) -> List[Dict[str, Any]]:
        """
        Search using Brave Search API
        
        Args:
            query: Search query string
            count: Number of results to return (default: 5)
            
        Returns:
            List of search results
        """
params = {
    "q": f"{query} news",  # 在查询中添加 news 关键词来筛选新闻
    "count": count
}
        
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    self.base_url,
                    headers=self.headers,
                    params=params,
                    timeout=10
                )
                
                # Debug logging
                print(f'Request URL: {response.url}')
                print(f'Request headers: {json.dumps(self.headers, default=str)}')
                
                response.raise_for_status()
                data = response.json()
                
                # Process and return results
                if isinstance(data, dict) and 'web' in data and 'results' in data['web']:
                    return [{
                        'title': result.get('title', ''),
                        'url': result.get('url', ''),
                        'description': result.get('description', ''),
                        'published': result.get('published', '')
                    } for result in data['web']['results'][:count]]
                else:
                    print(f'Unexpected response format: {json.dumps(data, indent=2)}')
                    return []
                    
            except requests.RequestException as e:
                print(f'Error in Brave Search (attempt {attempt + 1}/{self.max_retries}): {e}')
                if hasattr(e, 'response') and e.response is not None:
                    print(f'Response status: {e.response.status_code}')
                    print(f'Response content: {e.response.text}')
                if attempt < self.max_retries - 1:
                    sleep(self.retry_delay)
                continue
                
            except Exception as e:
                print(f'Unexpected error in Brave Search: {e}')
                return []
        
        return []  # Return empty list if all retries failed
