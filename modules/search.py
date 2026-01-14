import requests
import os
import sys
from tavily import TavilyClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import (
    GOOGLE_SEARCH_KEY_0, CX_ID_0,
    GOOGLE_SEARCH_KEY_1, CX_ID_1,
    TAVILY_SEARCH_KEY
)

class SearchEngine:
    """
    A unified search engine that intelligently switches between Google Custom Search 
    and Tavily Search based on API key availability and quota limits.
    
    Search Strategy:
    1. Start with Google Search Key 0
    2. If Key 0 is exhausted, switch to Key 1
    3. If both Google keys are exhausted, fallback to Tavily Search
    """
    
    def __init__(self):
        # Google Search Configuration
        self.google_keys = [
            {"api_key": GOOGLE_SEARCH_KEY_0, "cx_id": CX_ID_0, "exhausted": False},
            {"api_key": GOOGLE_SEARCH_KEY_1, "cx_id": CX_ID_1, "exhausted": False}
        ]
        self.current_google_key_index = 0
        
        # Tavily Search Configuration
        self.tavily_client = None
        if TAVILY_SEARCH_KEY:
            self.tavily_client = TavilyClient(api_key=TAVILY_SEARCH_KEY)
        
        self.using_tavily = False
    
    def search(self, query, num_results=7):
        """
        Search for links using the best available search provider.
        
        Args:
            query (str): The search query
            num_results (int): Number of results to return (default: 7)
            
        Returns:
            list: List of dictionaries containing 'title' and 'link'/'url' keys
        """
        # If already using Tavily, continue with it
        if self.using_tavily:
            return self._search_tavily(query, num_results)
        
        # Try Google Search with available keys
        for attempt in range(len(self.google_keys)):
            current_key = self.google_keys[self.current_google_key_index]
            
            if current_key["exhausted"]:
                # Move to next key
                self._switch_google_key()
                continue
            
            results = self._search_google(
                query, 
                current_key["api_key"], 
                current_key["cx_id"], 
                num_results
            )
            
            # If we got results, return them
            if results is not None:
                return results
            
            # If search failed (likely quota exceeded), mark key as exhausted
            print(f"Google Search Key {self.current_google_key_index} exhausted. Switching...")
            current_key["exhausted"] = True
            self._switch_google_key()
        
        # All Google keys exhausted, fallback to Tavily
        print("All Google Search keys exhausted. Switching to Tavily Search.")
        self.using_tavily = True
        return self._search_tavily(query, num_results)
    
    def _search_google(self, query, api_key, cx_id, num_results):
        """
        Perform a Google Custom Search.
        
        Returns:
            list or None: List of results if successful, None if quota exceeded/error
        """
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": cx_id,
            "q": query,
            "num": min(num_results, 10)  # Google API max is 10 per request
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            
            # Check for quota exceeded (403) or rate limit errors
            if response.status_code in [403, 429]:
                return None
            
            response.raise_for_status()
            data = response.json()
            
            # Handle cases where search returns 0 results
            if 'items' not in data:
                return []
            
            # Extract clean results
            clean_results = []
            for item in data['items']:
                clean_results.append({
                    "title": item.get("title"),
                    "link": item.get("link")
                })
            
            print(f"Google Search returned {len(clean_results)} results.")
            return clean_results
        
        except requests.exceptions.RequestException as e:
            print(f"Google Search error: {e}")
            return None
    
    def _search_tavily(self, query, num_results):
        """
        Perform a Tavily Search.
        
        Returns:
            list: List of results with 'title' and 'link' keys
        """
        if not self.tavily_client:
            print("Tavily Search is not configured (missing API key).")
            return []
        
        try:
            print(f"Using Tavily Search for: {query}")
            print(f"Tavily client initialized: {self.tavily_client is not None}")
            response = self.tavily_client.search(
                query, 
                search_depth="basic", 
                max_results=num_results, 
                include_images=False
            )
            
            results = []
            for result in response.get('results', []):
                results.append({
                    "title": result['title'],
                    "link": result['url']  # Note: Tavily uses 'url' instead of 'link'
                })
            
            print(f"Tavily Search returned {len(results)} results.")
            return results
        
        except Exception as e:
            print(f"Tavily Search error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _switch_google_key(self):
        """Switch to the next available Google Search key."""
        self.current_google_key_index = (self.current_google_key_index + 1) % len(self.google_keys)
    
    def reset_google_keys(self):
        """Reset all Google Search keys to non-exhausted state."""
        for key in self.google_keys:
            key["exhausted"] = False
        self.current_google_key_index = 0
        self.using_tavily = False
        print("Google Search keys have been reset.")
    
    def get_status(self):
        """Get the current status of the search engine."""
        status = {
            "current_provider": "Tavily" if self.using_tavily else f"Google (Key {self.current_google_key_index})",
            "google_keys_status": [
                f"Key {i}: {'Exhausted' if key['exhausted'] else 'Active'}"
                for i, key in enumerate(self.google_keys)
            ],
            "tavily_available": self.tavily_client is not None
        }
        return status

'''
# Backwards compatibility: create a default instance
_default_search_engine = SearchEngine()

def search(query, num_results=7):
    """
    Convenience function for searching with the default search engine instance.
    
    Args:
        query (str): The search query
        num_results (int): Number of results to return
        
    Returns:
        list: List of search results
    """
    return _default_search_engine.search(query, num_results)
'''
'''
# --- TEST ZONE ---
if __name__ == "__main__":
    # Initialize the search engine
    search_engine = SearchEngine()
    
    # Test query
    test_query = "Latest developments in quantum computing 2025"
    
    print("=" * 60)
    print(f"Testing UnifiedSearchEngine with query: '{test_query}'")
    print("=" * 60)
    
    # Check initial status
    print("\nInitial Status:")
    status = search_engine.get_status()
    print(f"  Current Provider: {status['current_provider']}")
    print(f"  Google Keys: {status['google_keys_status']}")
    print(f"  Tavily Available: {status['tavily_available']}")
    
    # Perform search
    print("\n" + "-" * 60)
    results = search_engine.search(test_query, num_results=5)
    print("-" * 60)
    
    # Display results
    print(f"\nFound {len(results)} results:")
    for idx, result in enumerate(results, 1):
        print(f"\n{idx}. {result['title']}")
        print(f"   Link: {result['link']}")
    
    # Check final status
    print("\n" + "=" * 60)
    print("Final Status:")
    final_status = search_engine.get_status()
    print(f"  Current Provider: {final_status['current_provider']}")
    print(f"  Google Keys: {final_status['google_keys_status']}")
    print("=" * 60)
'''
