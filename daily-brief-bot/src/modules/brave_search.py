import requests
import json

class BraveSearch:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = 'https://api.search.brave.com/web/search'  # Changed to web/search endpoint
        self.headers = {
            'Accept': 'application/json',
            'X-Brave-API-Key': api_key  # Using correct header name
        }
    
    def search(self, query, count=5):
        """Search news using Brave Search API"""
        params = {
            'q': query,
            'count': count,
            'type': 'news',  # Specify news search
            'freshness': 'day'  # Get recent news only
        }
        
        try:
            response = requests.get(
                self.base_url,
                headers=self.headers,
                params=params
            )
            
            # Print request details for debugging
            print(f'Request URL: {response.url}')
            print(f'Request headers: {json.dumps(self.headers)}')
            
            response.raise_for_status()
            data = response.json()
            
            # Extract and format news items
            if 'news' in data:
                return data['news']
            elif 'webPages' in data:  # Fallback to web results if no news
                return data['webPages']['value']
            return []
            
        except requests.RequestException as e:
            print(f'Error in Brave Search: {e}')
            if hasattr(e.response, 'text'):
                print(f'Response content: {e.response.text}')
            return []
        except Exception as e:
            print(f'Unexpected error in Brave Search: {e}')
            return []
