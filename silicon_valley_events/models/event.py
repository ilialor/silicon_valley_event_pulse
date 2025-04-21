
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict

@dataclass
class Event:
    """Base class for event data"""
    id: str
    title: str
    description: str
    start_time: datetime
    end_time: Optional[datetime]
    location: str
    url: str
    source: str
    tags: List[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "location": self.location,
            "url": self.url,
            "source": self.source,
            "tags": self.tags or []
        }
