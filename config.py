"""
Configuration settings for Daily Brief Bot
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Email Configuration
EMAIL_CONFIG = {
    'SMTP_SERVER': 'smtp.yeah.net',
    'SMTP_PORT': 465,
    'SENDER_EMAIL': os.getenv('EMAIL_HOST_USER'),
    'SENDER_PASSWORD': os.getenv('EMAIL_HOST_PASSWORD'),
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
    'swearchan@yeah.net',
    # Add more subscribers here
]

# Analysis Settings
ANALYSIS_SETTINGS = {
    'max_content_length': 1000,
    'min_similarity_score': 0.7,
    'max_recommendations': 10,
}