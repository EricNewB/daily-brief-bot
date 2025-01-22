"""
Content filter using Claude API to analyze and select valuable information
"""
import os
from typing import List, Dict
import anthropic

class ClaudeFilter:
    def __init__(self):
        self.client = anthropic.Client(api_key=os.getenv('ANTHROPIC_API_KEY'))
        
    def analyze_content(self, items: List[Dict]) -> List[Dict]:
        """
        Analyze content items using Claude API and return the most valuable ones
        
        Args:
            items: List of content items with title, url, and source
            
        Returns:
            List of 5 most valuable items with added value_score
        """
        # Prepare content for Claude
        content_text = "Please analyze these content items and select the 5 most valuable ones. Consider:\n\n"
        content_text += "1. Information density and uniqueness\n"
        content_text += "2. Long-term value vs temporary buzz\n"
        content_text += "3. Technical depth and educational value\n"
        content_text += "4. Practical applicability\n"
        content_text += "5. Credibility of source and discussion\n\n"
        
        content_text += "Content items:\n"
        for i, item in enumerate(items, 1):
            content_text += f"{i}. Title: {item['title']}\n"
            content_text += f"   Source: {item['source']}\n"
            if 'score' in item:
                content_text += f"   Score: {item['score']}\n"
            if 'hot_value' in item:
                content_text += f"   Hot Value: {item['hot_value']}\n"
            content_text += "\n"
            
        content_text += "\nPlease analyze each item and return your selection of the top 5 most valuable items in this format:\n"
        content_text += "1. [Index]: [Brief reason for selection]\n"
        content_text += "2. [Index]: [Brief reason for selection]\n"
        content_text += "..."
        
        try:
            # Call Claude API
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1024,
                temperature=0,
                system="你需要筛选出5条最有价值的信息。评判标准是信息密度、长期价值、技术深度、实用性、来源可信度。",
                messages=[{
                    "role": "user",
                    "content": content_text
                }]
            )
            
            # Parse Claude's response
            selected_indices = []
            for line in response.content[0].text.split('\n'):
                if line.strip() and line[0].isdigit():
                    index = int(line.split(':')[0].strip().split('.')[1])
                    selected_indices.append(index - 1)  # Convert to 0-based index
                    
            # Add value scores and sort
            scored_items = []
            for i, item in enumerate(items):
                if i in selected_indices:
                    rank = selected_indices.index(i)
                    item['value_score'] = 5 - rank  # 5 is highest, 1 is lowest
                    scored_items.append(item)
                    
            return sorted(scored_items, key=lambda x: x['value_score'], reverse=True)
            
        except Exception as e:
            print(f"Error calling Claude API: {str(e)}")
            # Return original items if analysis fails
            return items[:5]
            
    def filter_valuable_content(self, hacker_news: List[Dict], weibo: List[Dict]) -> List[Dict]:
        """
        Filter and select most valuable content from multiple sources
        
        Args:
            hacker_news: List of HackerNews items
            weibo: List of Weibo items
            
        Returns:
            List of 5 most valuable items across all sources
        """
        # Combine all items
        all_items = hacker_news + weibo
        
        # Analyze and select top 5
        valuable_items = self.analyze_content(all_items)
        
        return valuable_items[:5]