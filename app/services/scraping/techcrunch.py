from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging
import re

from app.db.session import SessionLocal
from app.models.models import Source, Event, ScrapingLog

logger = logging.getLogger(__name__)

class TechCrunchScraper:
    """
    Скрапер для сбора данных о событиях с TechCrunch
    """
    
    def __init__(self):
        self.base_url = "https://techcrunch.com"
        self.events_url = f"{self.base_url}/events/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self.db = SessionLocal()
        
    def __del__(self):
        self.db.close()
    
    def search_events(self) -> List[Dict]:
        """
        Поиск событий на TechCrunch
            
        Returns:
            Список словарей с информацией о событиях
        """
        events = []
        
        try:
            # Создаем лог скрейпинга
            source = self.db.query(Source).filter(Source.type == "techcrunch").first()
            if not source:
                source = Source(
                    name="TechCrunch",
                    url="https://techcrunch.com/events/",
                    type="techcrunch",
                    status="active"
                )
                self.db.add(source)
                self.db.commit()
                self.db.refresh(source)
            
            scraping_log = ScrapingLog(
                source_id=source.source_id,
                status="running",
                message="Started scraping TechCrunch events"
            )
            self.db.add(scraping_log)
            self.db.commit()
            self.db.refresh(scraping_log)
            
            start_time = datetime.utcnow()
            
            # Выполняем запрос
            response = requests.get(self.events_url, headers=self.headers)
            response.raise_for_status()
            
            # Парсим HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Находим все карточки событий
            event_cards = soup.select('.event-card')
            
            if not event_cards:
                # Альтернативный селектор, если структура страницы изменилась
                event_cards = soup.select('.tc-event-card')
            
            if not event_cards:
                # Еще один альтернативный селектор
                event_cards = soup.select('article.post')
            
            for card in event_cards:
                try:
                    # Извлекаем данные о событии
                    event_url_elem = card.select_one('a')
                    event_url = event_url_elem['href'] if event_url_elem else None
                    
                    if not event_url:
                        continue
                    
                    # Формируем полный URL события
                    if not event_url.startswith('http'):
                        event_url = f"{self.base_url}{event_url}"
                    
                    # Получаем детальную информацию о событии
                    event_data = self._get_event_details(event_url)
                    
                    if event_data:
                        events.append(event_data)
                        
                        # Сохраняем событие в базу данных
                        self._save_event(event_data, source.source_id)
                
                except Exception as e:
                    logger.error(f"Error processing event card: {str(e)}")
            
            # Обновляем лог скрейпинга
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            scraping_log.status = "success"
            scraping_log.message = f"Successfully scraped {len(events)} events from TechCrunch"
            scraping_log.events_found = len(events)
            scraping_log.execution_time = execution_time
            self.db.commit()
            
            # Обновляем источник
            source.last_checked = datetime.utcnow()
            self.db.commit()
            
            return events
            
        except Exception as e:
            logger.error(f"Error scraping TechCrunch: {str(e)}")
            
            if 'scraping_log' in locals():
                scraping_log.status = "error"
                scraping_log.message = f"Error scraping TechCrunch: {str(e)}"
                self.db.commit()
            
            return []
    
    def _get_event_details(self, event_url: str) -> Optional[Dict]:
        """
        Получение детальной информации о событии
        
        Args:
            event_url: URL события
            
        Returns:
            Словарь с информацией о событии или None в случае ошибки
        """
        try:
            response = requests.get(event_url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Извлекаем название события
            title_elem = soup.select_one('h1.article__title')
            if not title_elem:
                title_elem = soup.select_one('h1')
            title = title_elem.text.strip() if title_elem else "Unknown Event"
            
            # Извлекаем дату и время события
            date_elem = soup.select_one('.event-date')
            if not date_elem:
                date_elem = soup.select_one('.event-meta')
            date_str = date_elem.text.strip() if date_elem else ""
            
            start_datetime = None
            end_datetime = None
            
            if date_str:
                # Парсим дату и время (примерная логика, может потребоваться корректировка)
                date_patterns = [
                    r'(\w+ \d+(?:st|nd|rd|th)?, \d{4})',
                    r'(\w+ \d+, \d{4})',
                    r'(\d{2}/\d{2}/\d{4})'
                ]
                
                for pattern in date_patterns:
                    date_match = re.search(pattern, date_str)
                    if date_match:
                        date_part = date_match.group(1)
                        try:
                            # Удаляем суффиксы st, nd, rd, th
                            date_part = re.sub(r'(\d+)(?:st|nd|rd|th)', r'\1', date_part)
                            start_datetime = datetime.strptime(date_part, "%B %d, %Y")
                            break
                        except ValueError:
                            try:
                                start_datetime = datetime.strptime(date_part, "%m/%d/%Y")
                                break
                            except ValueError:
                                pass
            
            # Если не удалось распарсить дату, используем текущую дату
            if not start_datetime:
                start_datetime = datetime.utcnow()
                
            # Для TechCrunch событий обычно указывается только дата, поэтому
            # устанавливаем время начала на 9:00 и время окончания на 18:00
            start_datetime = start_datetime.replace(hour=9, minute=0, second=0, microsecond=0)
            end_datetime = start_datetime.replace(hour=18, minute=0, second=0, microsecond=0)
            
            # Извлекаем локацию
            location_elem = soup.select_one('.event-location')
            if not location_elem:
                location_elem = soup.select_one('.event-meta')
            location = location_elem.text.strip() if location_elem else "Silicon Valley"
            
            # Определяем, является ли событие виртуальным
            is_virtual = "online" in location.lower() or "virtual" in location.lower()
            
            # Извлекаем описание
            description_elem = soup.select_one('.article-content')
            if not description_elem:
                description_elem = soup.select_one('.article__content')
            description = description_elem.text.strip() if description_elem else ""
            
            # Извлекаем организатора
            organizer = "TechCrunch"  # По умолчанию для TechCrunch событий
            
            # Формируем данные о событии
            event_data = {
                "name": title,
                "description": description,
                "start_datetime_utc": start_datetime,
                "end_datetime_utc": end_datetime,
                "location_text": location,
                "is_virtual": is_virtual,
                "virtual_url": event_url if is_virtual else None,
                "original_url": event_url,
                "organizer": organizer
            }
            
            return event_data
            
        except Exception as e:
            logger.error(f"Error getting event details from {event_url}: {str(e)}")
            return None
    
    def _save_event(self, event_data: Dict, source_id: int) -> None:
        """
        Сохранение события в базу данных
        
        Args:
            event_data: Данные о событии
            source_id: ID источника
        """
        try:
            # Проверяем, существует ли уже событие с таким URL
            existing_event = self.db.query(Event).filter(
                Event.original_url == event_data["original_url"]
            ).first()
            
            if existing_event:
                # Обновляем существующее событие
                for key, value in event_data.items():
                    setattr(existing_event, key, value)
                
                self.db.commit()
                logger.info(f"Updated existing event: {event_data['name']}")
            else:
                # Создаем новое событие
                new_event = Event(
                    source_id=source_id,
                    **event_data
                )
                
                self.db.add(new_event)
                self.db.commit()
                logger.info(f"Added new event: {event_data['name']}")
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving event to database: {str(e)}")
