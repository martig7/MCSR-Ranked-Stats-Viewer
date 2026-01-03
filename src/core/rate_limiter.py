"""
Rate limiting functionality for MCSR Ranked API requests.
Provides sliding window rate limiting with persistence.
"""

import time
import json
import os
from typing import Dict
from collections import deque


class RateLimitTracker:
    """Track API request rate limiting with sliding window."""
    
    def __init__(self, max_requests: int = 500, window_minutes: int = 10):
        self.max_requests = max_requests
        self.window_seconds = window_minutes * 60
        self.requests = deque()
    
    def can_make_request(self) -> bool:
        """Check if we can make a request without hitting rate limit"""
        now = time.time()
        # Remove requests older than the window
        while self.requests and self.requests[0] < now - self.window_seconds:
            self.requests.popleft()
        
        return len(self.requests) < self.max_requests
    
    def record_request(self):
        """Record that a request was made"""
        self.requests.append(time.time())
    
    def get_wait_time(self) -> float:
        """Get seconds to wait before next request is allowed"""
        if self.can_make_request():
            return 0.0
        
        # Find the oldest request that needs to expire
        now = time.time()
        oldest_relevant = now - self.window_seconds
        
        if self.requests and self.requests[0] > oldest_relevant:
            return self.requests[0] - oldest_relevant
        return 0.0
    
    def get_status(self) -> Dict:
        """Get current rate limit status"""
        now = time.time()
        # Clean old requests
        while self.requests and self.requests[0] < now - self.window_seconds:
            self.requests.popleft()
        
        return {
            'requests_made': len(self.requests),
            'requests_remaining': self.max_requests - len(self.requests),
            'window_seconds': self.window_seconds,
            'can_request': self.can_make_request(),
            'wait_time': self.get_wait_time()
        }


def load_rate_limit_state(rate_limiter: RateLimitTracker, filename: str):
    """Load rate limit state from file"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
                # Restore request timestamps that are still relevant
                now = time.time()
                window_start = now - rate_limiter.window_seconds
                
                for timestamp in data.get('request_timestamps', []):
                    if timestamp > window_start:
                        rate_limiter.requests.append(timestamp)
    except Exception:
        # Silently fail and start fresh
        pass


def save_rate_limit_state(rate_limiter: RateLimitTracker, filename: str):
    """Save rate limit state to file"""
    try:
        # Clean old requests first
        now = time.time()
        while rate_limiter.requests and rate_limiter.requests[0] < now - rate_limiter.window_seconds:
            rate_limiter.requests.popleft()
        
        data = {
            'request_timestamps': list(rate_limiter.requests),
            'last_updated': now
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f)
    except Exception:
        # Silently fail - rate limiting will still work without persistence
        pass