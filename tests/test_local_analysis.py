"""
Local content analyzer for testing without API dependency
"""
import os
import sys
import json
import jieba
import re
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer

class LocalContentAnalyzer:
    def __init__(self):
        # 预定义的内容类型关键词
        self.type_keywords = {
            'tech': ['programming', 'software', 'hardware', 'algorithm', 'development', 'code', 
                    '编程', '软件', '硬件', '算法', '开发', '代码'],
            'business': ['market', 'industry', 'company', 'startup', 'investment',
                        '市场', '产业', '公司', '创业', '投资'],
            'science': ['research', 'study', 'discovery', 'experiment', 'innovation',
                       '研究', '科学', '发现', '实验', '创新'],
            'social': ['society', 'people', 'community', 'culture', 'life',
                      '社会', '人们', '社区', '文化', '生活']
        }

    def is_chinese(self, text):
        """检查文本是否主要是中文"""
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        return len(chinese_chars) > len(text) / 3

    def extract_keywords(self, text, top_k=5):
        """提取关键词"""
        if self.is_chinese(text):
            # 中文分词
            words = jieba.cut(text)
            words = [w for w in words if len(w) > 1]  # 过滤单字词
        else:
            # 英文分词
            words = re.findall(r'\w+', text.lower())
        
        # 统计词频
        word_freq = Counter(words)
        return [word for word, _ in word_freq.most_common(top_k)]

    def determine_content_type(self, text):
        """确定内容类型"""
        text = text.lower()
        type_scores = {}
        
        for content_type, keywords in self.type_keywords.items():
            score = sum(1 for keyword in keywords if keyword.lower() in text)
            type_scores[content_type] = score
        
        if not any(type_scores.values()):
            return 'general'
        return max(type_scores.items(), key=lambda x: x[1])[0]

    def estimate_complexity(self, text):
        """估计内容复杂度"""
        # 基于句子长度、专业词汇等估计复杂度
        sentences = re.split(r'[.。!！?？]', text)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
        
        if avg_sentence_length > 20:
            return 5
        elif avg_sentence_length > 15:
            return 4
        elif avg_sentence_length > 10:
            return 3
        elif avg_sentence_length > 5:
            return 2
        return 1

    def estimate_read_time(self, text):
        """估计阅读时间（分钟）"""
        # 假设中文每分钟阅读300字，英文每分钟阅读200词
        if self.is_chinese(text):
            return max(1, len(text) // 300)
        words = len(text.split())
        return max(1, words // 200)

    def analyze_content(self, content):
        """分析内容"""
        # 合并标题和摘要
        full_text = f"{content['title']} {content.get('summary', '')}"
        
        # 提取关键词作为标签
        tags = self.extract_keywords(full_text)
        
        # 确定内容类型
        content_type = self.determine_content_type(full_text)
        
        # 估计复杂度
        complexity = self.estimate_complexity(full_text)
        
        # 估计阅读时间
        read_time = self.estimate_read_time(full_text)
        
        # 从标签中选择主要话题
        topics = tags[:3]
        
        # 确定目标受众
        target_audience = {
            'tech': 'Developers and tech enthusiasts',
            'business': 'Business professionals and entrepreneurs',
            'science': 'Researchers and science enthusiasts',
            'social': 'General public',
            'general': 'General readers'
        }[content_type]

        return {
            "topics": topics,
            "tags": tags,
            "content_type": content_type,
            "target_audience": target_audience,
            "complexity": complexity,
            "read_time": read_time
        }

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
    analyzer = LocalContentAnalyzer()
    
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