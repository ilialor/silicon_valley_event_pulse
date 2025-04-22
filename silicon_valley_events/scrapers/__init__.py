
# Импортируем базовые классы
from .base import BaseEventSpider, SeleniumEventScraper

# Импортируем конкретные реализации пауков
from .stanford_events import StanfordEventsSpider
from .eventbrite_selenium import EventbriteSelenium
from .linkedin_events import LinkedInEventsScraper
from .meetup_selenium import MeetupSelenium
from .techcrunch_selenium import TechCrunchSelenium
from .meetup_events import MeetupEventsSpider

# Определяем публичный API модуля
__all__ = ['BaseEventSpider', 'SeleniumEventScraper', 'StanfordEventsSpider', 
           'EventbriteSelenium', 'LinkedInEventsScraper', 'MeetupEventsSpider',
           'MeetupSelenium', 'TechCrunchSelenium']



