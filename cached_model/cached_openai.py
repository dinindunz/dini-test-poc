# strands/models/cached_openai.py
import hashlib
import json
import time
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass
import threading

from strands.models.openai import OpenAIModel

@dataclass
class CacheEntry:
    """Represents a cached prompt-response pair."""
    response: Any
    timestamp: float
    access_count: int = 0
    last_accessed: float = None
    
    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.timestamp

class MemoryCache:
    """In-memory cache backend with LRU eviction."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[CacheEntry]:
        with self._lock:
            entry = self._cache.get(key)
            if entry:
                entry.access_count += 1
                entry.last_accessed = time.time()
            return entry
    
    def set(self, key: str, entry: CacheEntry) -> None:
        with self._lock:
            if len(self._cache) >= self.max_size:
                self._evict_lru()
            self._cache[key] = entry
    
    def delete(self, key: str) -> None:
        with self._lock:
            self._cache.pop(key, None)
    
    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
    
    def size(self) -> int:
        return len(self._cache)
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._cache:
            return
        
        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].last_accessed
        )
        del self._cache[lru_key]

class PromptCache:
    """Prompt caching system for Strands models."""
    
    def __init__(
        self,
        backend: Optional[MemoryCache] = None,
        ttl_seconds: Optional[int] = 3600,  # 1 hour default
        enable_cache: bool = True,
        cache_key_fields: List[str] = None
    ):
        self.backend = backend or MemoryCache()
        self.ttl_seconds = ttl_seconds
        self.enable_cache = enable_cache
        self.cache_key_fields = cache_key_fields or [
            'model_id', 'messages', 'temperature', 'max_tokens'
        ]
    
    def generate_cache_key(self, **kwargs) -> str:
        """Generate a deterministic cache key from request parameters."""
        cache_data = {}
        for field in self.cache_key_fields:
            if field in kwargs:
                cache_data[field] = kwargs[field]
        
        cache_str = json.dumps(cache_data, sort_keys=True, default=str)
        return hashlib.sha256(cache_str.encode()).hexdigest()[:16]
    
    def get(self, cache_key: str) -> Optional[Any]:
        """Get cached response if available and not expired."""
        if not self.enable_cache:
            return None
        
        entry = self.backend.get(cache_key)
        if not entry:
            return None
        
        # Check if entry is expired
        if self.ttl_seconds and (time.time() - entry.timestamp) > self.ttl_seconds:
            self.backend.delete(cache_key)
            return None
        
        return entry.response
    
    def set(self, cache_key: str, response: Any) -> None:
        """Store response in cache."""
        if not self.enable_cache:
            return
        
        entry = CacheEntry(
            response=response,
            timestamp=time.time()
        )
        self.backend.set(cache_key, entry)

class CachedOpenAIModel(OpenAIModel):
    """OpenAI model with built-in prompt caching."""
    
    def __init__(
        self,
        client_args: Dict[str, Any] = None,
        model_id: str = "gpt-4o",
        params: Dict[str, Any] = None,
        cache_config: Dict[str, Any] = None,
        **kwargs
    ):
        # Initialize parent OpenAI model
        super().__init__(
            client_args=client_args,
            model_id=model_id,
            params=params,
            **kwargs
        )
        
        # Initialize caching
        cache_config = cache_config or {}
        self.cache = PromptCache(
            ttl_seconds=cache_config.get('ttl_seconds', 3600),
            enable_cache=cache_config.get('enable', True),
            cache_key_fields=cache_config.get('key_fields', None)
        )
        
        # Cache statistics
        self._cache_hits = 0
        self._cache_misses = 0
    
    def _generate_cache_key(self, messages: List[Dict], **kwargs) -> str:
        """Generate cache key for the request."""
        request_params = {
            'model_id': self.model_id,
            'messages': messages,
            'temperature': kwargs.get('temperature', self.params.get('temperature')),
            'max_tokens': kwargs.get('max_tokens', self.params.get('max_tokens')),
            'top_p': kwargs.get('top_p', self.params.get('top_p'))
        }
        return self.cache.generate_cache_key(**request_params)
    
    def generate(self, messages: List[Dict], **kwargs) -> Any:
        """Override generate method to add caching."""
        # Generate cache key
        cache_key = self._generate_cache_key(messages, **kwargs)
        
        # Try to get from cache first
        cached_response = self.cache.get(cache_key)
        if cached_response is not None:
            self._cache_hits += 1
            return cached_response
        
        # Execute original generate method
        self._cache_misses += 1
        response = super().generate(messages, **kwargs)
        
        # Store in cache
        self.cache.set(cache_key, response)
        
        return response
    
    def cache_stats(self) -> Dict[str, Any]:
        """Get caching statistics."""
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hits': self._cache_hits,
            'misses': self._cache_misses,
            'hit_rate_percent': round(hit_rate, 2),
            'total_requests': total_requests,
            'cache_size': self.cache.backend.size(),
            'cache_enabled': self.cache.enable_cache,
            'ttl_seconds': self.cache.ttl_seconds
        }
    
    def clear_cache(self) -> None:
        """Clear the model's cache."""
        self.cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
