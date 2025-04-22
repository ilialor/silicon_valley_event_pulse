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

class EventbriteEventsSpider(BaseEventSpider):
    """
    Паук для сбора событий с сайта Eventbrite
    """
    name = "eventbrite_events"
    allowed_domains = ["www.eventbrite.com"]
    # Исправляем URL на более подходящий для GET-запроса
    # Замените текущий URL на:
    start_urls = ["https://www.eventbrite.com/d/ca--san-francisco/events/"]
    
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
        logger.info(f"Обработка страницы Eventbrite {self.current_page} из {self.max_pages}")
        
        # Получаем все карточки событий на странице
        event_cards = response.css('div.search-event-card-wrapper, article.event-card')
        
        logger.info(f"Найдено {len(event_cards)} событий на странице Eventbrite")
        
        for card in event_cards:
            event_link = card.css('a.event-card-link::attr(href), a.eds-event-card-content__action-link::attr(href)').get()
            if event_link:
                # Проверяем, является ли ссылка относительной
                if not event_link.startswith('http'):
                    event_link = response.urljoin(event_link)
                yield response.follow(event_link, self.parse_event)
            
        # Переход на следующую страницу, если она есть и не превышен лимит
        if self.current_page < self.max_pages:
            next_page = response.css('a[data-spec="page-next"]::attr(href)').get()
            if next_page:
                self.current_page += 1
                yield response.follow(next_page, self.parse)
    
    def parse_event(self, response):
        """
        Парсинг страницы отдельного события
        """
        try:
            # Извлекаем основную информацию о событии
            title = response.css('h1.event-title::text, h1.eds-text-hl::text').get()
            title = self.clean_text(title) if title else "Без названия"
            
            # Извлекаем описание события
            description_parts = response.css('div.event-description ::text, div.eds-text-bs::text').getall()
            description = ' '.join(description_parts).strip()
            description = self.clean_text(description)
            
            # Пытаемся извлечь дату из JSON-LD
            json_ld = response.css('script[type="application/ld+json"]::text').get()
            start_date = None
            end_date = None
            
            if json_ld:
                try:
                    data = json.loads(json_ld)
                    if isinstance(data, list):
                        data = data[0]
                    
                    if 'startDate' in data:
                        start_date = datetime.fromisoformat(data['startDate'].replace('Z', '+00:00'))
                    if 'endDate' in data:
                        end_date = datetime.fromisoformat(data['endDate'].replace('Z', '+00:00'))
                except (json.JSONDecodeError, ValueError) as e:
                    logger.error(f"Ошибка при парсинге JSON-LD: {str(e)}")
            
            # Если не удалось извлечь дату из JSON-LD, пробуем из текста
            if not start_date:
                date_str = response.css('time::text, p.date-info::text').get('')
                if date_str:
                    start_date = self.extract_date(date_str)
            
            # Если всё ещё нет даты, используем текущую
            if not start_date:
                start_date = datetime.now()
                
            # Извлекаем местоположение
            location = response.css('div.event-details__data::text, p.location-info::text').get('')
            location = self.clean_text(location)
            
            # Генерируем уникальный ID для события
            event_id = str(uuid.uuid4())
            
            # URL события
            url = response.url
            
            # Дополнительная информация
            organizer = response.css('a.js-d-scroll-to::text, a.organizer-name::text').get('')
            organizer = self.clean_text(organizer)
            
            # Извлекаем теги
            tags = response.css('a.js-event-categories::text, a.event-category::text').getall()
            tags = [self.clean_text(tag) for tag in tags if tag and self.clean_text(tag)]
            
            # Добавляем стандартный тег для всех событий Eventbrite
            if 'eventbrite' not in [t.lower() for t in tags]:
                tags.append('eventbrite')
            
            # Извлекаем URL изображения
            image_url = response.css('picture img::attr(src), img.event-logo::attr(src)').get('')
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
                end_time=end_date,
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
            
            logger.info(f"Собрано событие Eventbrite: {title}")
            return event
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге события Eventbrite: {str(e)}")
            return None
    
    def closed(self, reason):
        """
        Вызывается при завершении работы паука
        """
        logger.info(f"Паук {self.name} завершил работу. Причина: {reason}")
        logger.info(f"Всего собрано событий Eventbrite: {self.event_count}")
    
    # В класс EventbriteEventsSpider добавьте:
    handle_httpstatus_list = [405, 403, 404]  # Обрабатывать эти статусы
    
    def errback_httpbin(self, failure):
        """Обработка ошибок HTTP"""
        logger.error(f"Ошибка при запросе: {failure}")
        if failure.check(HttpError):
            response = failure.value.response
            logger.error(f"HTTP ошибка {response.status} для URL {response.url}")
            # Попробуйте альтернативный URL
            if response.status == 405 and "eventbrite.com" in response.url:
                alt_url = "https://www.eventbrite.com/d/ca--san-francisco/events/"
                logger.info(f"Пробуем альтернативный URL: {alt_url}")
                return scrapy.Request(alt_url, callback=self.parse)
    
    # В методе start_requests добавьте:
    def start_requests(self):
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        
        for url in self.start_urls:
            yield scrapy.Request(url=url, headers=headers, callback=self.parse)