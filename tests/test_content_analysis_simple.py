"""
Simplified test script for content analysis using Claude API
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import anthropic
from datetime import datetime
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SimpleContentAnalyzer:
    def __init__(self):
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        # 修改初始化方式
        self.client = anthropic.Anthropic(
            api_key=api_key
        )

    def analyze_content(self, content):
        """
        Analyze content using Claude API
        
        Args:
            content (dict): Content to analyze
            
        Returns:
            dict: Analysis results
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
        {json.dumps(content, indent=2, ensure_ascii=False)}
        
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
            # 修改API调用方式
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # 修改结果提取方式
            analysis = json.loads(response.content[0].text)
            return analysis
        except Exception as e:
            print(f"Error analyzing content: {str(e)}")
            return None

def main():
    """Test content analysis with sample data"""
    # Sample test data
    test_contents = [
        {
            "platform": "HackerNews",
            "title": "Rust Is The Future of JavaScript Infrastructure",
            "url": "https://example.com/article1",
            "summary": "An exploration of why Rust is becoming increasingly popular in building JavaScript tools and infrastructure. The article discusses performance benefits, memory safety, and developer experience improvements."
        },
        {
            "platform": "Weibo",
            "title": "今日北京人工智能大会开幕，多家科技公司发布重磅产品",
            "url": "https://example.com/post1",
            "summary": "在今天开幕的北京人工智能大会上，各大科技公司展示了最新的AI技术成果。其中包括自动驾驶、智能助手等多个领域的创新产品。与会专家表示，中国AI技术正在快速发展。"
        }
    ]
    
    # Initialize analyzer
    analyzer = SimpleContentAnalyzer()
    
    # Test with sample content
    print("\nTesting content analysis...")
    for content in test_contents:
        print(f"\nAnalyzing content from {content['platform']}:")
        print(f"Title: {content['title']}")
        analysis = analyzer.analyze_content(content)
        print("\nAnalysis results:")
        print(json.dumps(analysis, indent=2, ensure_ascii=False))
        print("\n" + "="*50)

if __name__ == '__main__':
    main()