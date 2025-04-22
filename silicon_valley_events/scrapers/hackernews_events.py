import scrapy
import logging
from datetime import datetime
from typing import List, Optional
from ..models.event import Event
from .base import BaseEventSpider
import re
import uuid

logger = logging.getLogger(__name__)

class HackerNewsEventsSpider(BaseEventSpider):
    """
    Паук для сбора событий с сайта Hacker News
    """
    name = "hackernews_events"
    allowed_domains = ["news.ycombinator.com"]
    start_urls = ["https://news.ycombinator.com/"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events = []
        self.event_count = 0
        self.max_pages = kwargs.get('max_pages', 3)
        self.current_page = 1
    
    def parse(self, response):
        """
        Парсинг страницы со списком новостей
        """
        logger.info(f"Обработка страницы HackerNews {self.current_page} из {self.max_pages}")
        
        # Получаем все новости на странице
        news_items = response.css('tr.athing')
        
        logger.info(f"Найдено {len(news_items)} новостей на странице HackerNews")
        
        for item in news_items:
            item_id = item.css('::attr(id)').get()
            if item_id:
                # Получаем заголовок и ссылку
                title = item.css('span.titleline > a::text').get()
                url = item.css('span.titleline > a::attr(href)').get()
                
                # Получаем информацию о времени и авторе из следующего tr
                subtext = response.css(f'tr#{"".join(["", item_id])}-subtext')
                time_str = subtext.css('span.age::attr(title)').get('')
                author = subtext.css('a.hnuser::text').get('')
                
                # Создаем событие
                event_id = str(uuid.uuid4())
                start_date = self.extract_date(time_str) if time_str else datetime.now()
                
                # Проверяем, содержит ли заголовок ключевые слова, связанные с событиями
                event_keywords = ['meetup', 'conference', 'event', 'hackathon', 'workshop', 'webinar', 'talk']
                is_event = any(keyword in title.lower() for keyword in event_keywords) if title else False
                
                # Если это похоже на событие, добавляем его в список
                if is_event:
                    event = Event(
                        id=event_id,
                        title=title,
                        description=f"Автор: {author}" if author else "",
                        start_time=start_date,
                        end_time=None,
                        location="Silicon Valley",
                        url=url,
                        source=self.name,
                        tags=["hackernews", "tech"],
                        image_url=None,
                        organizer=author,
                        is_online=False
                    )
                    
                    self.events.append(event)
                    self.event_count += 1
                    
                    logger.info(f"Собрано событие HackerNews: {title}")
            
        # Переход на следующую страницу, если она есть и не превышен лимит
        if self.current_page < self.max_pages:
            next_page = response.css('a.morelink::attr(href)').get()
            if next_page:
                self.current_page += 1
                yield response.follow(next_page, self.parse)
    
    def closed(self, reason):
        """
        Вызывается при завершении работы паука
        """
        logger.info(f"Паук {self.name} завершил работу. Причина: {reason}")
        logger.info(f"Всего собрано событий HackerNews: {self.event_count}")