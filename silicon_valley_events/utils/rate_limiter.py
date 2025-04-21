
from datetime import datetime
import asyncio

class RateLimiter:
    """Rate limiting utility"""
    def __init__(self, calls_per_minute: int):
        self.calls_per_minute = calls_per_minute
        self.calls = []
    
    async def wait_if_needed(self):
        now = datetime.now()
        self.calls = [call_time for call_time in self.calls 
                     if (now - call_time).total_seconds() < 60]
        
        if len(self.calls) >= self.calls_per_minute:
            wait_time = 60 - (now - self.calls[0]).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        self.calls.append(now)
