"""
Test the hybrid content analyzer
"""
import os
import asyncio
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analysis.hybrid_analyzer import HybridContentAnalyzer

# Load environment variables
load_dotenv()

async def main():
    print("\nTesting hybrid content analyzer...")
    analyzer = HybridContentAnalyzer()
    
    # Test content samples
    test_contents = [
        {
            'title': 'Rust Is The Future of JavaScript Infrastructure',
            'text': '''
            The JavaScript ecosystem is increasingly being built on Rust. From package managers (cargo-install) to bundlers (SWC), 
            transpilers (Babel's Rust port), and more, Rust is becoming the go-to language for JavaScript infrastructure.
            This shift brings better performance and memory safety while maintaining ease of use.
            '''
        },
        {
            'title': '今日北京人工智能大会开幕，多家科技公司发布重磅产品',
            'text': '''
            在今天举行的北京人工智能大会上，多家领先科技公司展示了他们最新的AI产品和解决方案。
            包括自动驾驶技术、智能医疗诊断系统、以及新一代大语言模型等。专家表示，这些创新将
            推动人工智能技术在更多领域的实际应用。
            '''
        }
    ]
    
    for content in test_contents:
        print(f"\nAnalyzing content: {content['title']}")
        try:
            result = await analyzer.analyze(content)
            print("\nAnalysis results:")
            print(f"Analysis source: {result['source']}")
            print(f"Content type: {result['content_type']}")
            if 'topics' in result:
                print(f"Topics: {result['topics']}")
            print(f"Keywords: {[k['word'] for k in result['keywords']]}")
            print(f"Complexity: {result['complexity']}")
            print(f"Reading time: {result['reading_time']} minutes")
            if 'sentiment' in result:
                print(f"Sentiment: {result['sentiment']}")
            if 'summary' in result:
                print(f"Summary: {result['summary']}")
        except Exception as e:
            print(f"Error analyzing content: {e}")
        print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
