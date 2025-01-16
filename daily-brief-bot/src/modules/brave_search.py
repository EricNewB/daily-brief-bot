import requests

class BraveSearch:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = 'https://api.search.brave.com/res/v1/news'
        self.headers = {
            'Accept': 'application/json',
            'X-Subscription-Token': api_key
        }
    
    def search(self, query, count=5):
        """Search news using Brave Search API"""
        params = {
            'q': query,
            'count': count
        }
        
        try:
            response = requests.get(
                self.base_url,
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f'Error in Brave Search: {e}')
            return None