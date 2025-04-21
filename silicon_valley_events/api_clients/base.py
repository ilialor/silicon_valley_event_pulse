
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List
from ..models.event import Event

class EventSource(ABC):
    """Abstract base class for event sources"""
    def __init__(self, name: str, rate_limit: int = 60):
        self.name = name
        self.rate_limit = rate_limit
    
    @abstractmethod
    async def fetch_events(self, start_date: datetime, end_date: datetime) -> List[Event]:
        pass
    
    @abstractmethod
    async def validate_source(self) -> bool:
        pass
