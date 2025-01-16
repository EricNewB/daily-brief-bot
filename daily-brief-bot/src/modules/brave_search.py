"""
Brave Search API implementation for daily-brief-bot.
Handles web search requests using the Brave Search API.
"""

import os
from typing import Dict, List, Optional, Union
import requests
from requests.exceptions import RequestException

class BraveSearchError(Exception):
    """Custom exception for Brave Search related errors."""
    pass

class BraveSearch:
    """
    A client for the Brave Search API.
    
    Attributes:
        api_key (str): The Brave Search API key
        base_url (str): The base URL for the Brave Search API
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Brave Search client.
        
        Args:
            api_key (str, optional): The API key for Brave Search.
                If not provided, will attempt to read from BRAVE_API_KEY environment variable.
        
        Raises:
            BraveSearchError: If no API key is provided or found in environment variables.
        """
        self.api_key = api_key or os.getenv('BRAVE_API_KEY')
        if not self.api_key:
            raise BraveSearchError("No API key provided. Set BRAVE_API_KEY environment variable or pass key to constructor.")
        
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        
    def search(self, query: str, count: int = 10) -> Dict[str, Union[List[Dict], int]]:
        """
        Perform a web search using Brave Search API.
        
        Args:
            query (str): The search query.
            count (int, optional): Number of results to return. Defaults to 10.
                Maximum allowed by API is 20.
        
        Returns:
            Dict containing:
                - results: List of search result dictionaries
                - total_count: Total number of results found
        
        Raises:
            BraveSearchError: If the API request fails or returns an error.
        """
        try:
            # Prepare headers and parameters
            headers = {
                "Accept": "application/json",
                "X-Subscription-Token": self.api_key
            }
            
            params = {
                "q": query,
                "count": min(count, 20)  # Ensure we don't exceed API limit
            }
            
            # Make the API request
            response = requests.get(
                self.base_url,
                headers=headers,
                params=params,
                timeout=30
            )
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse the response
            data = response.json()
            
            # Extract and format results
            results = []
            if "web" in data and "results" in data["web"]:
                for item in data["web"]["results"]:
                    result = {
                        "title": item.get("title", ""),
                        "description": item.get("description", ""),
                        "url": item.get("url", ""),
                        "published": item.get("published", "")
                    }
                    results.append(result)
            
            return {
                "results": results,
                "total_count": len(results)
            }
            
        except RequestException as e:
            raise BraveSearchError(f"Failed to perform search: {str(e)}")
        except (KeyError, ValueError) as e:
            raise BraveSearchError(f"Failed to parse search results: {str(e)}")
        except Exception as e:
            raise BraveSearchError(f"An unexpected error occurred: {str(e)}")

    def news_search(self, query: str, count: int = 10) -> Dict[str, Union[List[Dict], int]]:
        """
        Perform a news search using Brave Search API.
        Adds news-specific terms to the query to improve relevance of news results.
        
        Args:
            query (str): The search query.
            count (int, optional): Number of results to return. Defaults to 10.
        
        Returns:
            Dict containing:
                - results: List of news result dictionaries
                - total_count: Total number of results found
        """
        # Append news-specific terms to improve relevance for news content
        news_query = f"{query} news article recent"
        return self.search(news_query, count)
