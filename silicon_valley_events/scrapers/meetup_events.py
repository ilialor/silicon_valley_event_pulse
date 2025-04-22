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

class MeetupEventsSpider(BaseEventSpider):
    """
    Паук для сбора событий с сайта Meetup
    """
    name = "meetup_events"
    allowed_domains = ["www.meetup.com"]
    start_urls = ["https://www.meetup.com/find/?location=us--ca--silicon-valley&source=EVENTS"]
    
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
        logger.info(f"Обработка страницы Meetup {self.current_page} из {self.max_pages}")
        
        # Получаем все карточки событий на странице
        event_cards = response.css('div.eventCard, div.event-card')
        
        logger.info(f"Найдено {len(event_cards)} событий на странице Meetup")
        
        for card in event_cards:
            event_link = card.css('a.eventCard--link::attr(href), a.event-card-link::attr(href)').get()
            if event_link:
                # Проверяем, является ли ссылка относительной
                if not event_link.startswith('http'):
                    event_link = response.urljoin(event_link)
                yield response.follow(event_link, self.parse_event)
            
        # Переход на следующую страницу, если она есть и не превышен лимит
        if self.current_page < self.max_pages:
            next_page = response.css('a.pagination-next::attr(href), button.pagination-next::attr(data-url)').get()
            if next_page:
                self.current_page += 1
                yield response.follow(next_page, self.parse)
    
    def parse_event(self, response):
        """
        Парсинг страницы отдельного события
        """
        try:
            # Извлекаем основную информацию о событии
            title = response.css('h1.event-title::text, h1.pageTitle::text').get()
            title = self.clean_text(title) if title else "Без названия"
            
            # Извлекаем описание события
            description_parts = response.css('div.event-description ::text, div.eventDescription::text').getall()
            description = ' '.join(description_parts).strip()
            description = self.clean_text(description)
            
            # Извлекаем дату события
            date_str = response.css('time::text, span.eventTimeDisplay::text').get('')
            start_date = self.extract_date(date_str) if date_str else datetime.now()
            
            # Извлекаем местоположение
            location = response.css('div.event-location::text, address.venueDisplay::text').get('')
            location = self.clean_text(location)
            
            # Генерируем уникальный ID для события
            event_id = str(uuid.uuid4())
            
            # URL события
            url = response.url
            
            # Дополнительная информация
            organizer = response.css('div.event-host::text, div.groupNameLink::text').get('')
            organizer = self.clean_text(organizer)
            
            # Извлекаем теги
            tags = response.css('a.event-category::text, span.eventTag::text').getall()
            tags = [self.clean_text(tag) for tag in tags if tag and self.clean_text(tag)]
            
            # Добавляем стандартный тег для всех событий Meetup
            if 'meetup' not in [t.lower() for t in tags]:
                tags.append('meetup')
            
            # Извлекаем URL изображения
            image_url = response.css('img.event-image::attr(src), img.eventImage::attr(src)').get('')
            if image_url and not image_url.startswith('http'):
                image_url = response.urljoin(image_url)
            
            # Определяем, является ли событие онлайн
            is_online = False
            if location:
                is_online = any(keyword in location.lower() for keyword in ['online', 'zoom', 'virtual', 'webinar'])
            else:
                # Проверяем по заголовку или описанию
                is_online = any(keyword in (title + description).lower() for keyword in ['online', 'zoom', 'virtual', 'webinar'])
            
            # Создаем объект события
            event = Event(
                id=event_id,
                title=title,
                description=description,
                start_time=start_date,
                end_time=None,
                location=location,
                url=url,
                source=self.name,
                tags=tags,
                image_url=image_url,
                organizer=organizer,
                is_online=is_online
            )
            
            self.events.append(event)
            self.event_count += 1
            
            logger.info(f"Собрано событие Meetup: {title}")
            return event
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге события Meetup: {str(e)}")
            return None
    
    def closed(self, reason):
        """
        Вызывается при завершении работы паука
        """
        logger.info(f"Паук {self.name} завершил работу. Причина: {reason}")
        logger.info(f"Всего собрано событий Meetup: {self.event_count}")