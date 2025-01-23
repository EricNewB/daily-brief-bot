from datetime import datetime
from bs4 import BeautifulSoup
import markdown

class NewsProcessor:
    def clean_html(self, text):
        """Clean HTML from text"""
        if not text:
            return ''
        soup = BeautifulSoup(text, 'html.parser')
        return soup.get_text()
    
    def process(self, search_results):
        """Process raw search results into clean news items"""
        if not search_results or 'news' not in search_results:
            return []
        
        processed_items = []
        for item in search_results['news']:
            processed_item = {
                'title': self.clean_html(item.get('title', '')),
                'description': self.clean_html(item.get('description', '')),
                'url': item.get('url', ''),
                'source': item.get('source', 'Unknown'),
                'date': item.get('published_time', datetime.now().strftime('%Y-%m-%d'))
            }
            processed_items.append(processed_item)
        
        return processed_items