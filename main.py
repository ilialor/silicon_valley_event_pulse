
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Silicon Valley Events Collector
Приложение для сбора и агрегации технологических мероприятий в Силиконовой долине
из различных источников, включая Meetup, Eventbrite, LinkedIn и Stanford Events.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path
from scrapy.crawler import CrawlerProcess

# Настройка логирования
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
        
        # Если это Eventbrite и произошла ошибка API, используем скрейпер
        if source_name == 'eventbrite':
            # Collect from Eventbrite
            try:
                logger.info("Переключение на скрейпинг Eventbrite из-за ошибки API")
                from silicon_valley_events.scrapers.eventbrite_events import EventbriteEventsSpider
                
                process = CrawlerProcess({
                    'USER_AGENT': self.config['USER_AGENTS'][0],
                    'LOG_LEVEL': 'INFO',
                    'ROBOTSTXT_OBEY': False,  # Изменено с True на False
                    'DOWNLOAD_DELAY': 2
                })
                
                # Передаем класс, а не экземпляр
                process.crawl(EventbriteEventsSpider, max_pages=3)
                process.start()
                
                # Получаем экземпляр паука из процесса
                eventbrite_spider = next(iter(process.crawlers)).spider
                eventbrite_events = eventbrite_spider.events
                all_events.extend(eventbrite_events)
                logger.info(f"Собрано {len(eventbrite_events)} событий через скрейпинг Eventbrite")
            except Exception as scrape_error:
                logger.error(f"Ошибка при скрейпинге Eventbrite: {str(scrape_error)}")
        
        # Collect from LinkedIn
        # Collect from LinkedIn
        try:
            # Проверяем наличие учетных данных
            if 'LINKEDIN_EMAIL' not in self.config or 'LINKEDIN_PASSWORD' not in self.config:
                logger.warning("Отсутствуют учетные данные LinkedIn. Сбор событий с LinkedIn пропущен.")
            elif self.config['LINKEDIN_EMAIL'] == 'your_linkedin_email' or self.config['LINKEDIN_PASSWORD'] == 'your_linkedin_password':
                logger.warning("Учетные данные LinkedIn не настроены. Используйте реальные данные в config/settings.py")
            else:
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
            if hasattr(self, 'linkedin_scraper') and self.linkedin_scraper.driver:
                self.linkedin_scraper.close()
        
        # Collect from Stanford Events
        try:
            logger.info("Collecting events from Stanford")
            from silicon_valley_events.scrapers.stanford_events import StanfordEventsSpider
            
            process = CrawlerProcess({
                'USER_AGENT': self.config['USER_AGENTS'][0],
                'LOG_LEVEL': 'INFO',
                'ROBOTSTXT_OBEY': True,
                'DOWNLOAD_DELAY': 2,  # Задержка между запросами
                'CONCURRENT_REQUESTS': 8  # Количество одновременных запросов
            })
            
            # Создаем экземпляр паука с ограничением на количество страниц
            process.crawl(StanfordEventsSpider, max_pages=3)
            process.start()
            
            # Получаем экземпляр паука из процесса
            stanford_spider = next(iter(process.crawlers)).spider
            stanford_events = stanford_spider.events
            all_events.extend(stanford_events)
            logger.info(f"Collected {len(stanford_events)} events from Stanford")
        except Exception as e:
            error_msg = f"Error collecting events from Stanford: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        # Collect from HackerNews
        try:
            logger.info("Сбор событий с HackerNews")
            from silicon_valley_events.scrapers.hackernews_events import HackerNewsEventsSpider
            
            process = CrawlerProcess({
                'USER_AGENT': self.config['USER_AGENTS'][0],
                'LOG_LEVEL': 'INFO',
                'ROBOTSTXT_OBEY': False,  # Отключаем проверку robots.txt для эксперимента
                'DOWNLOAD_DELAY': 1
            })
            
            process.crawl(HackerNewsEventsSpider, max_pages=3)
            process.start()
            
            # Получаем экземпляр паука из процесса
            hackernews_spider = next(iter(process.crawlers)).spider
            hackernews_events = hackernews_spider.events
            all_events.extend(hackernews_events)
            logger.info(f"Собрано {len(hackernews_events)} событий с HackerNews")
        except Exception as e:
            error_msg = f"Ошибка при сборе событий с HackerNews: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        # Collect from Meetup
        # Collect from Meetup using Selenium
        try:
            logger.info("Сбор событий с Meetup через Selenium")
            from silicon_valley_events.scrapers.meetup_selenium import MeetupSeleniumScraper
            
            meetup_scraper = MeetupSeleniumScraper(headless=False, timeout=10, max_pages=3)
            meetup_events = await meetup_scraper.fetch_events(start_date, end_date)
            all_events.extend(meetup_events)
            logger.info(f"Собрано {len(meetup_events)} событий с Meetup через Selenium")
        except Exception as e:
            error_msg = f"Ошибка при сборе событий с Meetup через Selenium: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        # Collect from TechCrunch Events using Selenium
        try:
            logger.info("Сбор событий с TechCrunch Events через Selenium")
            from silicon_valley_events.scrapers.techcrunch_selenium import TechCrunchSeleniumScraper
            
            techcrunch_scraper = TechCrunchSeleniumScraper(headless=False, timeout=10, max_pages=3)
            techcrunch_events = await techcrunch_scraper.fetch_events(start_date, end_date)
            all_events.extend(techcrunch_events)
            logger.info(f"Собрано {len(techcrunch_events)} событий с TechCrunch Events через Selenium")
        except Exception as e:
            error_msg = f"Ошибка при сборе событий с TechCrunch Events через Selenium: {str(e)}"
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
        # В конфигурации добавьте больше User-Agent
        'USER_AGENTS': [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"
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

# В начале файла, после импортов
import os
from pathlib import Path

# Создаем директорию для логов, если она не существует
log_dir = Path('logs')
os.makedirs(log_dir, exist_ok=True)

# Настраиваем логирование в файл
file_handler = logging.FileHandler(log_dir / 'events_collector.log')
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Добавляем информацию о запуске
logger.info("=" * 50)
logger.info("Запуск сборщика событий")
logger.info("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
