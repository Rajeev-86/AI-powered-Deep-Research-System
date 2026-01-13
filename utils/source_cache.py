"""
Source Cache Manager - Caches frequently accessed URLs to avoid re-scraping
"""
import json
import os
import hashlib
from datetime import datetime, timedelta
from config.config import CHECKPOINT_DIR


class SourceCache:
    """Manages cached scraped content with TTL (Time To Live)."""
    
    def __init__(self, cache_ttl_hours=24):
        """
        Initialize source cache.
        
        Args:
            cache_ttl_hours (int): Hours before cache entries expire (default: 24)
        """
        self.cache_dir = os.path.join(CHECKPOINT_DIR, "source_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self.cache_index_path = os.path.join(self.cache_dir, "cache_index.json")
        
        # Load cache index
        self.cache_index = self._load_cache_index()
        
        # Stats
        self.hits = 0
        self.misses = 0
    
    def _load_cache_index(self):
        """Load cache index from disk."""
        if os.path.exists(self.cache_index_path):
            try:
                with open(self.cache_index_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"️  Error loading cache index: {e}")
                return {}
        return {}
    
    def _save_cache_index(self):
        """Save cache index to disk."""
        try:
            with open(self.cache_index_path, 'w', encoding='utf-8') as f:
                json.dump(self.cache_index, f, indent=2)
        except Exception as e:
            print(f"️  Error saving cache index: {e}")
    
    def _get_cache_key(self, url: str) -> str:
        """Generate a unique cache key for a URL."""
        return hashlib.md5(url.encode('utf-8')).hexdigest()
    
    def _is_expired(self, timestamp_str: str) -> bool:
        """Check if a cache entry has expired."""
        try:
            cached_time = datetime.fromisoformat(timestamp_str)
            return datetime.now() - cached_time > self.cache_ttl
        except:
            return True
    
    def get(self, url: str) -> str:
        """
        Get cached content for a URL.
        
        Args:
            url (str): The URL to look up
            
        Returns:
            str: Cached content if available and not expired, None otherwise
        """
        cache_key = self._get_cache_key(url)
        
        # Check if URL is in cache index
        if cache_key not in self.cache_index:
            self.misses += 1
            return None
        
        entry = self.cache_index[cache_key]
        
        # Check if cache has expired
        if self._is_expired(entry['timestamp']):
            self.misses += 1
            # Remove expired entry
            self.remove(url)
            return None
        
        # Try to load cached content
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.txt")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.hits += 1
                    return content
            except Exception as e:
                print(f"️  Error reading cache file: {e}")
                self.misses += 1
                return None
        else:
            self.misses += 1
            return None
    
    def put(self, url: str, content: str):
        """
        Cache content for a URL.
        
        Args:
            url (str): The URL to cache
            content (str): The scraped content
        """
        if not content:
            return
        
        cache_key = self._get_cache_key(url)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.txt")
        
        try:
            # Save content to file
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Update cache index
            self.cache_index[cache_key] = {
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'size_bytes': len(content)
            }
            
            self._save_cache_index()
            
        except Exception as e:
            print(f"️  Error caching content: {e}")
    
    def remove(self, url: str):
        """Remove a URL from cache."""
        cache_key = self._get_cache_key(url)
        
        # Remove from index
        if cache_key in self.cache_index:
            del self.cache_index[cache_key]
            self._save_cache_index()
        
        # Remove cache file
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.txt")
        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
            except Exception as e:
                print(f"️  Error removing cache file: {e}")
    
    def clear_expired(self):
        """Remove all expired cache entries."""
        expired_keys = []
        
        for cache_key, entry in self.cache_index.items():
            if self._is_expired(entry['timestamp']):
                expired_keys.append(cache_key)
        
        for cache_key in expired_keys:
            url = self.cache_index[cache_key]['url']
            self.remove(url)
        
        if expired_keys:
            print(f"️  Cleared {len(expired_keys)} expired cache entries")
    
    def clear_all(self):
        """Clear entire cache."""
        for cache_key in list(self.cache_index.keys()):
            url = self.cache_index[cache_key]['url']
            self.remove(url)
        
        print("️  Cache cleared")
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        total_size = sum(entry.get('size_bytes', 0) for entry in self.cache_index.values())
        
        return {
            'entries': len(self.cache_index),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'total_size_mb': total_size / (1024 * 1024)
        }
    
    def print_stats(self):
        """Print cache statistics."""
        stats = self.get_stats()
        print(f"\n Cache Statistics:")
        print(f"   Entries: {stats['entries']}")
        print(f"   Hits: {stats['hits']}")
        print(f"   Misses: {stats['misses']}")
        print(f"   Hit Rate: {stats['hit_rate']:.1f}%")
        print(f"   Total Size: {stats['total_size_mb']:.2f} MB")
    
    def should_cache(self, url: str) -> bool:
        """
        Determine if a URL should be cached based on domain quality.
        
        High-quality domains that should be cached:
        - Official documentation sites
        - GitHub repositories
        - Academic papers
        - Government sites
        """
        cache_worthy_domains = [
            'github.com', 'docs.', 'documentation.',
            '.edu', '.gov', '.org',
            'arxiv.org', 'wikipedia.org',
            'stackoverflow.com', 'python.org',
            'ai.google.dev', 'cloud.google.com',
            'openai.com', 'anthropic.com',
            'huggingface.co', 'paperswithcode.com'
        ]
        
        return any(domain in url.lower() for domain in cache_worthy_domains)
