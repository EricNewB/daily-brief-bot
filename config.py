"""
Configuration settings for Daily Brief Bot
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Email Configuration
EMAIL_CONFIG = {
    'SMTP_SERVER': os.getenv('SMTP_SERVER', 'smtp.yeah.net'),
    'SMTP_PORT': int(os.getenv('SMTP_PORT', '465')),
    'SMTP_USERNAME': os.getenv('SMTP_USERNAME'),
    'SMTP_PASSWORD': os.getenv('SMTP_PASSWORD'),
    'SENDER_EMAIL': os.getenv('EMAIL_USER'),
    'SENDER_PASSWORD': os.getenv('EMAIL_PASSWORD'),
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
    # WeChat source removed
    'max_content_length': 1000,  # Maximum content length for analysis
    'min_similarity_score': 0.7, # Minimum similarity score for content matching
    'max_recommendations': 10,   # Maximum number of recommendations per request
}

# Subscribers list
SUBSCRIBERS = [
    os.getenv('RECIPIENT_EMAIL', 'swearchan@yeah.net'),
    # Add more subscribers here
]

# Analysis Settings
ANALYSIS_SETTINGS = {
    'max_content_length': 1000,
    'min_similarity_score': 0.7,
    'max_recommendations': 10,
}