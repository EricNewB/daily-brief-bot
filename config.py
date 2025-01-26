"""
Configuration settings for Daily Brief Bot
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Email Configuration
EMAIL_CONFIG = {
    'SMTP_SERVER': os.environ['SMTP_SERVER'],
    'SMTP_PORT': int(os.environ['SMTP_PORT']),
    'SMTP_USERNAME': os.environ['SMTP_USERNAME'],
    'SMTP_PASSWORD': os.environ['SMTP_PASSWORD'],
    'SENDER_EMAIL': os.environ['SENDER_EMAIL'],
    'SENDER_PASSWORD': os.environ['SMTP_PASSWORD'],
}

# API Keys
API_KEYS = {
    'ANTHROPIC': os.getenv('ANTHROPIC_API_KEY'),
    'BRAVE': os.getenv('BRAVE_API_KEY'),
}

# Content Configuration
CONTENT_CONFIG = {
    'HACKER_NEWS_LIMIT': 10,    # Number of HackerNews stories to fetch
    'WEIBO_LIMIT': 10,          # Number of Weibo topics to fetch
    'max_content_length': 1000,  # Maximum content length for analysis
    'min_similarity_score': 0.7, # Minimum similarity score for content matching
    'max_recommendations': 10,   # Maximum number of recommendations per request
}

# User Interests Configuration
USER_INTERESTS = {
    'academic': {
        'topics': ['UX Design', 'Animation', 'AIGC', 'HCI', 'Digital Art'],
        'limit': 3,
        'keywords': ['research', 'study', 'conference', 'paper', 'design', 'animation', 'AI', 'generative'],
        'priority': 1
    },
    'international_news': {
        'countries': ['Korea', 'USA'],
        'limit': 3,
        'priority': 2,
        'keywords': ['politics', 'economy', 'technology', 'society'],
        'exclude_keywords': ['celebrity', 'entertainment']
    },
    'gaming': {
        'limit': 2,
        'priority': 3,
        'keywords': ['steam', 'sale', 'discount', 'game release', 'price drop'],
        'platforms': ['Steam', 'Epic Games']
    },
    'china_news': {
        'limit': 4,
        'priority': 2,
        'exclude_keywords': ['celebrity gossip', '网红', '明星绯闻'],
        'min_popularity': 100000  # 微博热度阈值
    }
}

# AI Model Configuration
AI_CONFIG = {
    'model': 'claude-3-haiku-20240307',  # 使用更经济的 haiku 模型
    'max_tokens': 1000,
    'temperature': 0.7
}

# Subscribers list
SUBSCRIBERS = [
    os.environ['RECIPIENT_EMAIL'],
    '659521082@qq.com',
    # Add more subscribers here
]

# Analysis Settings
ANALYSIS_SETTINGS = {
    'max_content_length': 1000,
    'min_similarity_score': 0.7,
    'max_recommendations': 10,
}
