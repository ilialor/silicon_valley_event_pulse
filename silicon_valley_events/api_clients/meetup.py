
import aiohttp
import logging
from datetime import datetime
from typing import List
from ..models.event import Event
from ..utils.rate_limiter import RateLimiter
from .base import EventSource

logger = logging.getLogger(__name__)

class MeetupAPI(EventSource):
    """Meetup API client"""
    BASE_URL = "https://api.meetup.com"
    
    def __init__(self, api_key: str):
        super().__init__("meetup", rate_limit=30)
        self.api_key = api_key
        self.rate_limiter = RateLimiter(self.rate_limit)
        self.session = None
    
    async def _init_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
    
    async def validate_source(self) -> bool:
        try:
            await self._init_session()
            params = {"page": 1, "per_page": 1}
            async with self.session.get(f"{self.BASE_URL}/find/upcoming_events", params=params) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Meetup API validation failed: {str(e)}")
            return False

    async def fetch_events(self, start_date: datetime, end_date: datetime) -> List[Event]:
        await self._init_session()
        events = []
        params = {
            "location": "Silicon Valley",
            "radius": "25",
            "topic_category": "tech",
            "start_date_range": start_date.isoformat(),
            "end_date_range": end_date.isoformat(),
            "page": 200
        }
        
        try:
            await self.rate_limiter.wait_if_needed()
            async with self.session.get(f"{self.BASE_URL}/find/upcoming_events", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    for event_data in data.get("events", []):
                        event = Event(
                            id=f"meetup_{event_data['id']}",
                            title=event_data['name'],
                            description=event_data.get('description', ''),
                            start_time=datetime.fromisoformat(event_data['local_date']),
                            end_time=None,
                            location=event_data.get('venue', {}).get('address', ''),
                            url=event_data['link'],
                            source="meetup",
                            tags=[g['name'] for g in event_data.get('group', {}).get('topics', [])]
                        )
                        events.append(event)
                else:
                    logger.error(f"Meetup API request failed with status {response.status}")
        except Exception as e:
            logger.error(f"Error fetching Meetup events: {str(e)}")
        
        return events
