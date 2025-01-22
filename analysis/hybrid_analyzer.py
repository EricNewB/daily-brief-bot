"""
Hybrid content analyzer that combines Claude API and local analysis
"""
import os
import json
from anthropic import Anthropic
import jieba
import jieba.analyse
from typing import Dict, Optional, Any, List
from difflib import SequenceMatcher

class HybridContentAnalyzer:
    def __init__(self):
        try:
            self.anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        except Exception as e:
            print(f"Error initializing Anthropic client: {e}")
            raise
        jieba.setLogLevel(20)  # Suppress jieba logging
        self._content_cache = []  # Cache for similarity checking
    
    def _check_similarity(self, content: Dict[str, str]) -> Optional[float]:
        """Check if content is similar to recently processed content"""
        if not self._content_cache:
            return None
            
        title = content.get('title', '')
        text = content.get('text', '')
        current_content = f"{title}\n{text}"
        
        max_similarity = 0.0
        for cached in self._content_cache:
            cached_title = cached.get('title', '')
            cached_text = cached.get('text', '')
            cached_content = f"{cached_title}\n{cached_text}"
            
            similarity = SequenceMatcher(None, current_content, cached_content).ratio()
            max_similarity = max(max_similarity, similarity)
        
        return max_similarity
    
    def _update_cache(self, content: Dict[str, str]) -> None:
        """Update the content cache for similarity checking"""
        self._content_cache.append(content)
        if len(self._content_cache) > 100:  # 限制缓存大小
            self._content_cache.pop(0)

    async def analyze(self, content: Dict[str, str], check_similarity: bool = True) -> Dict[str, Any]:
        """Analyze content and optionally check for similarity with recent content"""
        if check_similarity:
            similarity = self._check_similarity(content)
            if similarity and similarity > 0.8:  # 相似度阈值
                return {
                    'error': 'content_too_similar',
                    'similarity': similarity,
                    'source': 'similarity_check'
                }
            
        # 更新缓存
        self._update_cache(content)
        
        try:
            return await self._claude_analysis(content)
        except Exception as e:
            print(f"Claude API analysis failed: {e}")
            print("Falling back to local analysis...")
            return self._local_analysis(content)

    async def _claude_analysis(self, content: Dict[str, str]) -> Dict[str, Any]:
        """Analyze content using Claude API"""
        prompt = self._build_analysis_prompt(content)
        
        try:
            response = await self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            if hasattr(response, 'content') and response.content:
                response_text = response.content[0].text if isinstance(response.content, list) else response.content
            else:
                raise Exception("No content in Claude API response")

            analysis = json.loads(response_text)
            analysis['source'] = 'claude'
            return analysis

    def _build_analysis_prompt(self, content: Dict[str, str]) -> str:
        """Build prompt for Claude API analysis"""
        return f"""Please analyze the following content and return a JSON object with these fields:
- title: The content title
- keywords: Array of {{"word": string, "weight": number}} objects
- topics: Main topics discussed
- content_type: Type of content (news, tutorial, discussion, etc.)
- sentiment: Overall sentiment (positive, negative, neutral)
- complexity: Estimated complexity level (1-5)
- reading_time: Estimated reading time in minutes
- summary: Brief summary in original language
- language: Content language

Title: {content.get('title', '')}

Content:
{content.get('text', '')}

Return only valid JSON without any other text."""

    def _detect_content_type(self, text: str) -> str:
        """Simple rule-based content type detection"""
        markers = {
            'tutorial': ['how to', '教程', '步骤', 'step by step'],
            'news': ['报道', '消息', 'announced', 'released'],
            'discussion': ['讨论', '观点', 'opinion', 'thoughts'],
            'review': ['评测', '评价', 'review', 'pros and cons']
        }
        
        text = text.lower()
        for content_type, words in markers.items():
            if any(word in text for word in words):
                return content_type
        return 'article'

    def _estimate_complexity(self, text: str) -> int:
        """Estimate content complexity on a scale of 1-5"""
        # Enhanced complexity estimation based on multiple factors
        score = 0
        
        # 1. Sentence length analysis
        sentences = text.split('。')
        if sentences:
            avg_sentence_len = sum(len(s) for s in sentences) / len(sentences)
            if avg_sentence_len > 30: score += 1
            if avg_sentence_len > 50: score += 1
            if avg_sentence_len > 80: score += 1
        
        # 2. Technical terminology density
        technical_terms = {
            'basic': ['API', '算法', '架构', 'framework', '原理', '系统', '技术', 'cloud'],
            'advanced': ['并发', '异步', '分布式', '微服务', '容器化', '虚拟化', '中间件', '实例化'],
            'expert': ['一致性', '原子性', '隔离性', '持久性', '反向代理', '负载均衡', '服务网格', '编排']
        }
        
        term_score = 0
        for level, terms in technical_terms.items():
            count = sum(term in text for term in terms)
            if level == 'basic': term_score += count * 0.5
            elif level == 'advanced': term_score += count * 1.0
            elif level == 'expert': term_score += count * 1.5
        
        score += min(round(term_score), 3)
        
        # 3. Code snippet detection
        code_markers = ['```', 'def ', 'class ', 'import ', 'from ', '//']
        if any(marker in text for marker in code_markers):
            score += 1
        
        return min(max(score, 1), 5)
            
        except Exception as e:
            print(f"Error in Claude analysis: {str(e)}")
            raise

    def _local_analysis(self, content: Dict[str, str]) -> Dict[str, Any]:
        """Local content analysis using rule-based methods"""
        title = content.get('title', '')
        text = content.get('text', '')
        full_text = f"{title}\n{text}"
        
        # Extract keywords
        keywords = jieba.analyse.extract_tags(full_text, topK=10, withWeight=True)
        
        # Estimate reading time (words per minute)
        words = len(jieba.lcut(full_text))
        reading_time = round(words / 200)  # Assuming 200 words/minute
        
        # Simple content type detection
        content_type = self._detect_content_type(full_text)
        
        analysis = {
            'title': title,
            'keywords': [{'word': k, 'weight': w} for k, w in keywords],
            'content_type': content_type,
            'reading_time': reading_time,
            'complexity': self._estimate_complexity(full_text),
            'source': 'local'
        }
        
        return analysis