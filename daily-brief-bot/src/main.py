import os
import json
from datetime import datetime
from modules.brave_search import BraveSearch
from modules.email_sender import EmailSender
from modules.news_processor import NewsProcessor

def load_config():
    """Load user preferences from config file"""
    with open('config/preferences.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    # Load configuration
    config = load_config()
    
    # Initialize components
    brave_search = BraveSearch(os.getenv('BRAVE_API_KEY'))
    email_sender = EmailSender(
        username=os.getenv('EMAIL_USER'),
        password=os.getenv('EMAIL_PASSWORD')
    )
    news_processor = NewsProcessor()
    
    # Gather news based on preferences
    news_items = []
    for topic in config['topics']:
        results = brave_search.search(topic)
        processed_news = news_processor.process(results)
        news_items.extend(processed_news)
    
    # Generate and send email digest
    if news_items:
        subject = f"Daily Brief - {datetime.now().strftime('%Y-%m-%d')}"
        email_sender.send_digest(subject, news_items)

if __name__ == '__main__':
    main()