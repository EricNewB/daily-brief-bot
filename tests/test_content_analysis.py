"""
Test script for content analysis using Claude API
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawlers.hacker_news import HackerNewsCrawler
from crawlers.weibo import WeiboCrawler
from datetime import datetime
import json
import anthropic

class ContentAnalyzer:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    def analyze_content(self, content):
        """
        Analyze content using Claude API
        
        Args:
            content (dict): Content to analyze, should have 'title' and 'url' fields
            
        Returns:
            dict: Analysis results including topics, tags, and complexity
        """
        prompt = f"""
        Please analyze this content and provide the following information in JSON format:
        1. Main topics (up to 3)
        2. Tags (up to 5 keywords)
        3. Content type (tech, business, social, etc.)
        4. Target audience
        5. Complexity level (1-5)
        6. Estimated read time (in minutes)
        
        Content to analyze:
        Title: {content.get('title', '')}
        URL: {content.get('url', '')}
        
        Please provide your analysis in this JSON format:
        {{
            "topics": [],
            "tags": [],
            "content_type": "",
            "target_audience": "",
            "complexity": 0,
            "read_time": 0
        }}
        """
        
        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[{
                    "role": "system",
                    "content": "You are a content analysis expert. Analyze the given content and provide structured insights."
                }, {
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Extract JSON from response
            analysis = json.loads(response.content[0].text)
            return analysis
        except Exception as e:
            print(f"Error analyzing content: {str(e)}")
            return None

def main():
    """Test content analysis with real data"""
    # Initialize crawlers
    hn_crawler = HackerNewsCrawler()
    weibo_crawler = WeiboCrawler()
    
    # Get some test content
    hn_articles = hn_crawler.fetch_trending(2)
    weibo_posts = weibo_crawler.fetch_trending(2)
    
    # Initialize analyzer
    analyzer = ContentAnalyzer()
    
    # Test with HackerNews content
    print("\nAnalyzing HackerNews articles...")
    for article in hn_articles:
        print(f"\nArticle: {article['title']}")
        analysis = analyzer.analyze_content(article)
        print("Analysis:", json.dumps(analysis, indent=2, ensure_ascii=False))
    
    # Test with Weibo content
    print("\nAnalyzing Weibo posts...")
    for post in weibo_posts:
        print(f"\nPost: {post['title']}")
        analysis = analyzer.analyze_content(post)
        print("Analysis:", json.dumps(analysis, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()