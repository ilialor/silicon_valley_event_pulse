
import aiohttp
import logging
from datetime import datetime
from typing import List
from ..models.event import Event
from ..utils.rate_limiter import RateLimiter
from .base import EventSource

logger = logging.getLogger(__name__)

class EventbriteAPI(EventSource):
    """Eventbrite API client"""
    BASE_URL = "https://www.eventbriteapi.com/v3"
    
    def __init__(self, api_key: str):
        super().__init__("eventbrite", rate_limit=30)
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
            async with self.session.get(f"{self.BASE_URL}/users/me/") as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Eventbrite API validation failed: {str(e)}")
            return False

    async def fetch_events(self, start_date: datetime, end_date: datetime) -> List[Event]:
        await self._init_session()
        events = []
        params = {
            "location.address": "Silicon Valley",
            "location.within": "25mi",
            "categories": "102",
            "start_date.range_start": start_date.isoformat(),
            "start_date.range_end": end_date.isoformat(),
            "expand": "venue,category",
        }
        
        try:
            await self.rate_limiter.wait_if_needed()
            async with self.session.get(f"{self.BASE_URL}/events/search/", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    for event_data in data.get("events", []):
                        event = Event(
                            id=f"eventbrite_{event_data['id']}",
                            title=event_data['name']['text'],
                            description=event_data['description']['text'],
                            start_time=datetime.fromisoformat(event_data['start']['local']),
                            end_time=datetime.fromisoformat(event_data['end']['local']),
                            location=event_data.get('venue', {}).get('address', {}).get('localized_address_display', ''),
                            url=event_data['url'],
                            source="eventbrite",
                            tags=[event_data.get('category', {}).get('name', '')]
                        )
                        events.append(event)
                else:
                    logger.error(f"Eventbrite API request failed with status {response.status}")
        except Exception as e:
            logger.error(f"Error fetching Eventbrite events: {str(e)}")
        
        return events
