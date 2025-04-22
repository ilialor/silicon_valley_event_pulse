import scrapy
import logging
from datetime import datetime
from typing import List, Optional
from ..models.event import Event
from .base import BaseEventSpider
import re
import uuid
import json

logger = logging.getLogger(__name__)

class StanfordEventsSpider(BaseEventSpider):
    """
    Паук для сбора событий с сайта Stanford Events
    """
    name = "stanford_events"
    allowed_domains = ["events.stanford.edu"]
    start_urls = ["https://events.stanford.edu/"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events = []
        self.event_count = 0
        self.max_pages = kwargs.get('max_pages', 5)
        self.current_page = 1
    
    def parse(self, response):
        """
        Парсинг страницы со списком событий
        """
        logger.info(f"Обработка страницы Stanford Events {self.current_page} из {self.max_pages}")
        
        # Получаем все карточки событий на странице
        event_cards = response.css('div.event-card, div.event-item')
        
        logger.info(f"Найдено {len(event_cards)} событий на странице Stanford Events")
        
        for card in event_cards:
            event_link = card.css('a.event-link::attr(href), a.event-title::attr(href)').get()
            if event_link:
                # Проверяем, является ли ссылка относительной
                if not event_link.startswith('http'):
                    event_link = response.urljoin(event_link)
                yield response.follow(event_link, self.parse_event)
            
        # Переход на следующую страницу, если она есть и не превышен лимит
        if self.current_page < self.max_pages:
            next_page = response.css('a.next-page::attr(href), a.pagination-next::attr(href)').get()
            if next_page:
                self.current_page += 1
                yield response.follow(next_page, self.parse)
    
    def parse_event(self, response):
        """
        Парсинг страницы отдельного события
        """
        try:
            # Извлекаем основную информацию о событии
            title = response.css('h1.event-title::text, h1.title::text').get()
            title = self.clean_text(title) if title else "Без названия"
            
            # Извлекаем описание события
            description_parts = response.css('div.event-description ::text, div.description::text').getall()
            description = ' '.join(description_parts).strip()
            description = self.clean_text(description)
            
            # Извлекаем дату события
            date_str = response.css('time::text, span.date::text').get('')
            start_date = self.extract_date(date_str) if date_str else datetime.now()
            
            # Извлекаем местоположение
            location = response.css('div.location::text, span.location::text').get('')
            location = self.clean_text(location)
            
            # Генерируем уникальный ID для события
            event_id = str(uuid.uuid4())
            
            # URL события
            url = response.url
            
            # Дополнительная информация
            organizer = response.css('div.organizer::text, span.organizer::text').get('')
            organizer = self.clean_text(organizer)
            
            # Извлекаем теги
            tags = response.css('a.event-category::text, span.category::text').getall()
            tags = [self.clean_text(tag) for tag in tags if tag and self.clean_text(tag)]
            
            # Добавляем стандартный тег для всех событий Stanford
            if 'stanford' not in [t.lower() for t in tags]:
                tags.append('stanford')
            
            # Извлекаем URL изображения
            image_url = response.css('img.event-image::attr(src), img.featured-image::attr(src)').get('')
            if image_url and not image_url.startswith('http'):
                image_url = response.urljoin(image_url)
            
            # Создаем объект события
            event = Event(
                id=event_id,
                title=title,
                description=description,
                start_time=start_date,
                end_time=None,  # Конечная дата обычно не указана
                location=location,
                url=url,
                source=self.name,
                tags=tags,
                image_url=image_url,
                organizer=organizer,
                is_online=False  # По умолчанию считаем, что события не онлайн
            )
            
            self.events.append(event)
            self.event_count += 1
            
            logger.info(f"Собрано событие Stanford: {title}")
            return event
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге события Stanford: {str(e)}")
            return None
    
    def closed(self, reason):
        """
        Вызывается при завершении работы паука
        """
        logger.info(f"Паук {self.name} завершил работу. Причина: {reason}")
        logger.info(f"Всего собрано событий Stanford: {self.event_count}")