from typing import Dict, List, Optional
from datetime import datetime
import logging

from app.db.session import SessionLocal
from app.models.models import Event, EventAnalytics

logger = logging.getLogger(__name__)

class DataProcessor:
    """
    Модуль обработки и структурирования данных о событиях
    """
    
    def __init__(self):
        self.db = SessionLocal()
        
    def __del__(self):
        self.db.close()
    
    def process_events(self, limit: int = 100) -> List[Dict]:
        """
        Обработка событий, которые еще не были обработаны
        
        Args:
            limit: Максимальное количество событий для обработки за один раз
            
        Returns:
            Список обработанных событий
        """
        processed_events = []
        
        try:
            # Получаем события, которые еще не имеют аналитики
            events = self.db.query(Event).outerjoin(
                EventAnalytics, Event.event_id == EventAnalytics.event_id
            ).filter(
                EventAnalytics.analytics_id == None
            ).limit(limit).all()
            
            for event in events:
                try:
                    # Нормализация данных
                    processed_event = self._normalize_event_data(event)
                    
                    # Дедупликация (в будущем можно расширить)
                    # Сейчас дедупликация происходит на уровне скрейперов по URL
                    
                    processed_events.append(processed_event)
                    
                    logger.info(f"Processed event: {event.name}")
                    
                except Exception as e:
                    logger.error(f"Error processing event {event.event_id}: {str(e)}")
            
            return processed_events
            
        except Exception as e:
            logger.error(f"Error in process_events: {str(e)}")
            return []
    
    def _normalize_event_data(self, event: Event) -> Dict:
        """
        Нормализация данных о событии
        
        Args:
            event: Объект события
            
        Returns:
            Словарь с нормализованными данными о событии
        """
        # Нормализация названия (удаление лишних пробелов, приведение к единому регистру)
        name = event.name.strip()
        if name.isupper():
            name = name.title()
        
        # Нормализация описания
        description = event.description.strip() if event.description else ""
        
        # Нормализация локации
        location_text = event.location_text.strip() if event.location_text else ""
        
        # Нормализация организатора
        organizer = event.organizer.strip() if event.organizer else ""
        
        # Проверка и коррекция дат
        start_datetime_utc = event.start_datetime_utc
        end_datetime_utc = event.end_datetime_utc
        
        # Если дата окончания раньше даты начала или отсутствует, устанавливаем её на 2 часа позже начала
        if not end_datetime_utc or end_datetime_utc <= start_datetime_utc:
            from datetime import timedelta
            end_datetime_utc = start_datetime_utc + timedelta(hours=2)
            
            # Обновляем событие в базе данных
            event.end_datetime_utc = end_datetime_utc
            self.db.commit()
        
        # Формируем нормализованные данные
        normalized_data = {
            "event_id": event.event_id,
            "name": name,
            "description": description,
            "start_datetime_utc": start_datetime_utc,
            "end_datetime_utc": end_datetime_utc,
            "location_text": location_text,
            "is_virtual": event.is_virtual,
            "virtual_url": event.virtual_url,
            "original_url": event.original_url,
            "organizer": organizer,
            "source_id": event.source_id
        }
        
        return normalized_data
    
    def find_duplicate_events(self) -> List[Dict]:
        """
        Поиск дубликатов событий на основе названия, даты и места проведения
        
        Returns:
            Список групп дубликатов
        """
        duplicates = []
        
        try:
            # Получаем все события
            events = self.db.query(Event).all()
            
            # Создаем словарь для группировки потенциальных дубликатов
            event_groups = {}
            
            for event in events:
                # Создаем ключ для группировки на основе названия, даты и места
                # Используем только дату (без времени) для более гибкого сравнения
                key = (
                    event.name.lower(),
                    event.start_datetime_utc.date(),
                    event.location_text.lower() if event.location_text else ""
                )
                
                if key in event_groups:
                    event_groups[key].append(event)
                else:
                    event_groups[key] = [event]
            
            # Фильтруем группы, содержащие более одного события
            for key, group in event_groups.items():
                if len(group) > 1:
                    duplicate_group = []
                    for event in group:
                        duplicate_group.append({
                            "event_id": event.event_id,
                            "name": event.name,
                            "start_datetime_utc": event.start_datetime_utc,
                            "location_text": event.location_text,
                            "source_id": event.source_id,
                            "original_url": event.original_url
                        })
                    
                    duplicates.append(duplicate_group)
            
            return duplicates
            
        except Exception as e:
            logger.error(f"Error in find_duplicate_events: {str(e)}")
            return []
    
    def merge_duplicate_events(self, primary_event_id: int, duplicate_event_ids: List[int]) -> bool:
        """
        Объединение дубликатов событий
        
        Args:
            primary_event_id: ID основного события
            duplicate_event_ids: Список ID дубликатов
            
        Returns:
            True, если объединение прошло успешно, иначе False
        """
        try:
            # Получаем основное событие
            primary_event = self.db.query(Event).filter(Event.event_id == primary_event_id).first()
            
            if not primary_event:
                logger.error(f"Primary event with ID {primary_event_id} not found")
                return False
            
            # Получаем дубликаты
            duplicate_events = self.db.query(Event).filter(Event.event_id.in_(duplicate_event_ids)).all()
            
            # Объединяем информацию
            for duplicate in duplicate_events:
                # Если у основного события нет описания, но есть у дубликата
                if not primary_event.description and duplicate.description:
                    primary_event.description = duplicate.description
                
                # Если у основного события нет времени окончания, но есть у дубликата
                if not primary_event.end_datetime_utc and duplicate.end_datetime_utc:
                    primary_event.end_datetime_utc = duplicate.end_datetime_utc
                
                # Если у основного события нет координат, но есть у дубликата
                if not primary_event.location_lat and not primary_event.location_lon and duplicate.location_lat and duplicate.location_lon:
                    primary_event.location_lat = duplicate.location_lat
                    primary_event.location_lon = duplicate.location_lon
                
                # Удаляем дубликат
                self.db.delete(duplicate)
            
            self.db.commit()
            logger.info(f"Successfully merged duplicates into event {primary_event_id}")
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in merge_duplicate_events: {str(e)}")
            return False
