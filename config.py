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
