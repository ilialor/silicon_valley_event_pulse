
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path
from scrapy.crawler import CrawlerProcess

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EventCollector:
    """Main orchestrator for collecting Silicon Valley events"""
    
    def __init__(self, config: dict):
        try:
            # Import components only when collector is instantiated
            from silicon_valley_events.api_clients.meetup import MeetupAPI
            from silicon_valley_events.api_clients.eventbrite import EventbriteAPI
            from silicon_valley_events.scrapers.stanford_events import StanfordEventsSpider
            from silicon_valley_events.scrapers.linkedin_events import LinkedInEventsScraper
            from silicon_valley_events.models.database import EventStorage
            
            self.config = config
            self.storage = EventStorage(config.get('DATABASE_URL', 'sqlite:///events.db'))
            
            # Initialize API clients
            self.meetup_client = MeetupAPI(config['MEETUP_API_KEY'])
            self.eventbrite_client = EventbriteAPI(config['EVENTBRITE_API_KEY'])
            
            # Initialize scrapers
            self.linkedin_scraper = LinkedInEventsScraper(
                config['LINKEDIN_EMAIL'],
                config['LINKEDIN_PASSWORD']
            )
            
            self.sources = {
                'meetup': self.meetup_client,
                'eventbrite': self.eventbrite_client
            }
        except Exception as e:
            logger.error(f"Error initializing EventCollector: {str(e)}")
            raise
    
    async def validate_sources(self):
        """Validate all event sources are accessible"""
        validation_results = {}
        for source_name, source in self.sources.items():
            try:
                is_valid = await source.validate_source()
                validation_results[source_name] = is_valid
                if not is_valid:
                    logger.error(f"Source {source_name} validation failed")
            except Exception as e:
                logger.error(f"Error validating {source_name}: {str(e)}")
                validation_results[source_name] = False
        return validation_results
    
    async def collect_events(self, start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None) -> List['Event']:
        """Collect events from all sources"""
        if not start_date:
            start_date = datetime.now()
        if not end_date:
            end_date = start_date + timedelta(days=30)
        
        all_events = []
        errors = []
        
        # Collect from API sources
        for source_name, source in self.sources.items():
            try:
                logger.info(f"Collecting events from {source_name}")
                events = await source.fetch_events(start_date, end_date)
                all_events.extend(events)
                logger.info(f"Collected {len(events)} events from {source_name}")
            except Exception as e:
                error_msg = f"Error collecting events from {source_name}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # Collect from LinkedIn
        try:
            logger.info("Collecting events from LinkedIn")
            await self.linkedin_scraper.login()
            linkedin_events = await self.linkedin_scraper.fetch_events(start_date, end_date)
            all_events.extend(linkedin_events)
            logger.info(f"Collected {len(linkedin_events)} events from LinkedIn")
        except Exception as e:
            error_msg = f"Error collecting events from LinkedIn: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
        finally:
            self.linkedin_scraper.close()
        
        # Collect from Stanford Events
        try:
            logger.info("Collecting events from Stanford")
            process = CrawlerProcess({
                'USER_AGENT': self.config['USER_AGENTS'][0]
            })
            process.crawl(StanfordEventsSpider)
            process.start()
        except Exception as e:
            error_msg = f"Error collecting events from Stanford: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        # Save all collected events
        for event in all_events:
            try:
                self.storage.save_event(event)
            except Exception as e:
                error_msg = f"Error saving event {event.id}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        if errors:
            logger.warning(f"Collection completed with {len(errors)} errors")
        
        return all_events
    
    def get_calendar_events(self, start_date: datetime, end_date: datetime,
                          source: Optional[str] = None,
                          tag: Optional[str] = None) -> List['Event']:
        """Get events for calendar view with optional filtering"""
        try:
            return self.storage.get_events(start_date, end_date, source, tag)
        except Exception as e:
            logger.error(f"Error retrieving calendar events: {str(e)}")
            return []

async def main():
    # Load configuration
    config = {
        'MEETUP_API_KEY': 'your_meetup_api_key',
        'EVENTBRITE_API_KEY': 'your_eventbrite_api_key',
        'LINKEDIN_EMAIL': 'your_linkedin_email',
        'LINKEDIN_PASSWORD': 'your_linkedin_password',
        'DATABASE_URL': 'sqlite:///events.db',
        'USER_AGENTS': [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        ]
    }
    
    collector = EventCollector(config)
    
    # Validate sources
    validation_results = await collector.validate_sources()
    logger.info(f"Source validation results: {validation_results}")
    
    # Collect events for the next 30 days
    start_date = datetime.now()
    end_date = start_date + timedelta(days=30)
    
    events = await collector.collect_events(start_date, end_date)
    logger.info(f"Total events collected: {len(events)}")
    
    # Example of retrieving calendar events
    calendar_events = collector.get_calendar_events(start_date, end_date)
    logger.info(f"Total calendar events: {len(calendar_events)}")

if __name__ == "__main__":
    asyncio.run(main())
