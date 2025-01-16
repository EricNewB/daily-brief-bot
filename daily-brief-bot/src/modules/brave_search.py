"""
Brave Search API implementation for daily-brief-bot.
Handles web search requests using the Brave Search API with rate limiting and retry logic.
"""

import os
import time
from typing import Dict, List, Optional, Union
import requests
from requests.exceptions import RequestException
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class BraveSearchError(Exception):
    """Custom exception for Brave Search related errors."""
    pass

class BraveSearchRateLimitError(BraveSearchError):
    """Raised when the API rate limit is exceeded."""
    pass

class BraveSearch:
    """
    A client for the Brave Search API with rate limiting and retry logic.
    
    Attributes:
        api_key (str): The Brave Search API key
        base_url (str): The base URL for the Brave Search API
        last_request_time (float): Timestamp of the last API request
        min_request_interval (float): Minimum time between requests in seconds
    """
    
    def __init__(self, api_key: Optional[str] = None, min_request_interval: float = 1.0):
        """
        Initialize the Brave Search client.
        
        Args:
            api_key (str, optional): The API key for Brave Search.
                If not provided, will attempt to read from BRAVE_API_KEY environment variable.
            min_request_interval (float, optional): Minimum time between requests in seconds.
                Defaults to 1.0 seconds.
        
        Raises:
            BraveSearchError: If no API key is provided or found in environment variables.
        """
        self.api_key = api_key or os.getenv('BRAVE_API_KEY')
        if not self.api_key:
            raise BraveSearchError("No API key provided. Set BRAVE_API_KEY environment variable or pass key to constructor.")
        
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        self.last_request_time = 0
        self.min_request_interval = min_request_interval
    
    def _wait_for_rate_limit(self):
        """Ensure minimum time interval between requests."""
        now = time.time()
        time_since_last_request = now - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last_request)
        self.last_request_time = time.time()

    @retry(
        retry=retry_if_exception_type(BraveSearchRateLimitError),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        stop=stop_after_attempt(3)
    )
    def search(self, query: str, count: int = 10) -> Dict[str, Union[List[Dict], int]]:
        """
        Perform a web search using Brave Search API with automatic retry on rate limit errors.
        
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
            BraveSearchRateLimitError: If rate limit is exceeded (will trigger retry).
        """
        try:
            # Respect rate limiting
            self._wait_for_rate_limit()
            
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
            
            # Handle rate limiting explicitly
            if response.status_code == 429:
                raise BraveSearchRateLimitError(
                    "Rate limit exceeded. Retrying with exponential backoff..."
                )
            
            # Check for other HTTP errors
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
            if hasattr(e.response, 'status_code') and e.response.status_code == 429:
                raise BraveSearchRateLimitError(
                    "Rate limit exceeded. Retrying with exponential backoff..."
                )
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
