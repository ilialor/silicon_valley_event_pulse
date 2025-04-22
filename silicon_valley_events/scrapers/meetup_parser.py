import logging
import os
import re
import uuid
import traceback
import json
from datetime import datetime
from typing import List, Optional
from bs4 import BeautifulSoup

# Временный класс Event для тестирования
class Event:
    def __init__(self, title, description=None, start_date=None, end_date=None, 
                 location=None, url=None, image_url=None, source=None):
        self.id = str(uuid.uuid4())
        self.title = title
        self.description = description
        self.start_date = start_date
        self.end_date = end_date
        self.location = location
        self.url = url
        self.image_url = image_url
        self.source = source

# Настройка логирования
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('meetup_parser')

class MeetupParser:
    """
    Парсер для извлечения событий из сохраненной HTML-страницы Meetup Events
    """
    
    def __init__(self, html_file_path=None):
        """
        Инициализация парсера
        
        Args:
            html_file_path: Путь к сохраненному HTML-файлу
        """
        self.html_file_path = html_file_path or os.path.join(os.getcwd(), "meetup_main_page.html")
        logger.info(f"Инициализация парсера Meetup с файлом: {self.html_file_path}")
        
        # Создаем папку для сохранения страниц событий
        self.events_pages_dir = os.path.join(os.getcwd(), "meetup_events_pages")
        if not os.path.exists(self.events_pages_dir):
            try:
                os.makedirs(self.events_pages_dir)
                logger.info(f"Создана директория для страниц событий: {self.events_pages_dir}")
            except Exception as e:
                logger.error(f"Ошибка при создании директории для страниц событий: {str(e)}")
                self.events_pages_dir = os.getcwd()
    
    def parse_events(self):
        """
        Парсинг событий из сохраненного HTML-файла
        
        Returns:
            List[Event]: Список событий
        """
        try:
            # Проверка существования файла
            if not os.path.exists(self.html_file_path):
                logger.error(f"Файл {self.html_file_path} не найден")
                return []
            
            # Проверка прав доступа к файлу
            if not os.access(self.html_file_path, os.R_OK):
                logger.error(f"Нет прав на чтение файла: {self.html_file_path}")
                return []
            
            logger.info(f"Чтение HTML-файла: {self.html_file_path}")
            with open(self.html_file_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
                logger.info(f"HTML-файл успешно прочитан, размер: {len(html_content)} байт")
            
            # Создание объекта BeautifulSoup
            logger.info("Создание объекта BeautifulSoup для парсинга")
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Сохраняем полный HTML для отладки
            debug_html_path = os.path.join(self.events_pages_dir, "full_page_debug.html")
            with open(debug_html_path, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            logger.info(f"Сохранен полный HTML для отладки: {debug_html_path}")
            
            # Ищем структурированные данные о событии в JSON-LD
            events = []
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_ld_scripts:
                try:
                    json_data = json.loads(script.string)
                    if isinstance(json_data, dict) and '@type' in json_data and json_data['@type'] == 'Event':
                        logger.info(f"Найдены структурированные данные о событии в JSON-LD")
                        
                        # Извлекаем данные о событии
                        event_title = json_data.get('name', '')
                        event_description = json_data.get('description', '')
                        event_start_date = json_data.get('startDate')
                        event_end_date = json_data.get('endDate')
                        event_location = None
                        
                        # Обрабатываем местоположение
                        location_data = json_data.get('location', [])
                        if location_data:
                            if isinstance(location_data, list):
                                location_data = location_data[0]
                            
                            location_name = location_data.get('name', '')
                            address = location_data.get('address', {})
                            
                            address_parts = []
                            if location_name:
                                address_parts.append(location_name)
                            if address.get('streetAddress'):
                                address_parts.append(address.get('streetAddress'))
                            if address.get('addressLocality'):
                                address_parts.append(address.get('addressLocality'))
                            if address.get('addressRegion'):
                                address_parts.append(address.get('addressRegion'))
                            
                            event_location = ', '.join(address_parts)
                        
                        # Парсим даты
                        if event_start_date:
                            try:
                                event_start_date = datetime.fromisoformat(event_start_date.replace('Z', '+00:00'))
                            except ValueError:
                                event_start_date = None
                        
                        if event_end_date:
                            try:
                                event_end_date = datetime.fromisoformat(event_end_date.replace('Z', '+00:00'))
                            except ValueError:
                                event_end_date = None
                        
                        # Создаем объект события
                        event = Event(
                            title=event_title,
                            description=event_description,
                            start_date=event_start_date,
                            end_date=event_end_date,
                            location=event_location,
                            url=json_data.get('url', ''),
                            image_url=json_data.get('image', {}).get('url', '') if isinstance(json_data.get('image'), dict) else '',
                            source="Meetup Events (JSON-LD)"
                        )
                        
                        events.append(event)
                        logger.info(f"Событие успешно обработано из JSON-LD: {event_title}")
                except Exception as e:
                    logger.error(f"Ошибка при обработке JSON-LD: {str(e)}")
                    continue
            
            # Если нашли события в JSON-LD, возвращаем их
            if events:
                logger.info(f"Найдено {len(events)} событий в JSON-LD")
                return events
            
            # Пробуем различные селекторы для поиска событий на Meetup
            selectors = [
                '.event-card',
                '.eventCard',
                '.event-listing',
                '.event-listing-container',
                '.event-listing-card',
                '.event-card-wrapper',
                'div[data-event-id]',
                'div[data-testid="event-card"]',
                'div.flex-item.flex-item--shrink'
            ]
            
            for selector in selectors:
                logger.info(f"Поиск событий по селектору: {selector}")
                event_elements = soup.select(selector)
                
                if event_elements:
                    logger.info(f"Найдено {len(event_elements)} элементов по селектору: {selector}")
                    
                    for i, element in enumerate(event_elements, 1):
                        try:
                            # Сохраняем HTML элемента для отладки
                            element_debug_path = os.path.join(self.events_pages_dir, f"event_card_{i}.html")
                            with open(element_debug_path, 'w', encoding='utf-8') as f:
                                f.write(str(element))
                            
                            # Извлекаем данные о событии
                            event_title = self._extract_text(element, '.event-title, .event-name, h2, h3, [data-testid="event-title"]')
                            if not event_title:
                                continue
                            
                            event_url = self._extract_url(element, 'a')
                            event_description = self._extract_text(element, '.event-description, .description, [data-testid="event-description"]')
                            event_date_text = self._extract_text(element, '.event-date, .date, time, [data-testid="event-date"]')
                            event_location = self._extract_text(element, '.event-location, .location, [data-testid="event-venue"]')
                            event_image_url = self._extract_image_url(element, 'img')
                            
                            # Парсим дату
                            start_date, end_date = self._parse_date(event_date_text)
                            
                            # Создаем объект события
                            event = Event(
                                title=event_title,
                                description=event_description,
                                start_date=start_date,
                                end_date=end_date,
                                location=event_location,
                                url=event_url,
                                image_url=event_image_url,
                                source="Meetup Events"
                            )
                            
                            events.append(event)
                            logger.info(f"Событие успешно обработано: {event_title}")
                            
                        except Exception as e:
                            logger.error(f"Ошибка при обработке события {i}: {str(e)}")
                            traceback.print_exc()
                            continue
                    
                    # Если нашли события, прекращаем поиск по другим селекторам
                    if events:
                        break
            
            logger.info(f"Всего найдено {len(events)} событий")
            return events
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге событий: {str(e)}")
            traceback.print_exc()
            return []
    
    def update_event_details(self, event):
        """
        Обновление деталей события из страницы события
        
        Args:
            event: Объект события для обновления
        """
        try:
            # Проверка существования файла
            if not os.path.exists(self.html_file_path):
                logger.error(f"Файл {self.html_file_path} не найден")
                return
            
            # Чтение HTML-файла
            with open(self.html_file_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
            
            # Создание объекта BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Извлекаем более подробное описание
            description_element = soup.select_one('.event-description, [data-testid="event-description"]')
            if description_element and description_element.text.strip():
                event.description = description_element.text.strip()
            
            # Извлекаем более точную информацию о местоположении
            location_element = soup.select_one('.event-location, [data-testid="event-venue"]')
            if location_element and location_element.text.strip():
                event.location = location_element.text.strip()
            
            # Извлекаем более точную информацию о дате
            date_element = soup.select_one('.event-date, [data-testid="event-date"]')
            if date_element and date_element.text.strip():
                start_date, end_date = self._parse_date(date_element.text.strip())
                if start_date:
                    event.start_date = start_date
                if end_date:
                    event.end_date = end_date
            
            logger.info(f"Обновлены детали события: {event.title}")
        except Exception as e:
            logger.error(f"Ошибка при обновлении деталей события: {str(e)}")
    
    def _extract_text(self, element, selector):
        """
        Извлечение текста из элемента по селектору
        
        Args:
            element: Элемент BeautifulSoup
            selector: CSS-селектор
        
        Returns:
            str: Извлеченный текст или пустая строка
        """
        try:
            selected_element = element.select_one(selector)
            if selected_element:
                return selected_element.text.strip()
            return ""
        except Exception:
            return ""
    
    def _extract_url(self, element, selector):
        """
        Извлечение URL из элемента по селектору
        
        Args:
            element: Элемент BeautifulSoup
            selector: CSS-селектор
        
        Returns:
            str: Извлеченный URL или пустая строка
        """
        try:
            selected_element = element.select_one(selector)
            if selected_element and selected_element.has_attr('href'):
                url = selected_element['href']
                # Если URL относительный, добавляем базовый URL
                if url.startswith('/'):
                    url = f"https://www.meetup.com{url}"
                return url
            return ""
        except Exception:
            return ""
    
    def _extract_image_url(self, element, selector):
        """
        Извлечение URL изображения из элемента по селектору
        
        Args:
            element: Элемент BeautifulSoup
            selector: CSS-селектор
        
        Returns:
            str: Извлеченный URL изображения или пустая строка
        """
        try:
            selected_element = element.select_one(selector)
            if selected_element:
                if selected_element.has_attr('src'):
                    return selected_element['src']
                elif selected_element.has_attr('data-src'):
                    return selected_element['data-src']
            return ""
        except Exception:
            return ""
    
    def _parse_date(self, date_text):
        """
        Парсинг даты из текста
        
        Args:
            date_text: Текст с датой
        
        Returns:
            tuple: (start_date, end_date) - объекты datetime или None
        """
        if not date_text:
            return None, None
        
        try:
            # Пробуем различные форматы даты
            # Пример: "Monday, April 22, 2024 at 6:30 PM to 8:30 PM"
            date_match = re.search(r'(\w+, \w+ \d+, \d{4}) at (\d+:\d+ [AP]M)( to (\d+:\d+ [AP]M))?', date_text)
            if date_match:
                date_str = date_match.group(1)
                start_time_str = date_match.group(2)
                end_time_str = date_match.group(4) if date_match.group(3) else None
                
                # Парсим дату начала
                start_datetime_str = f"{date_str} {start_time_str}"
                start_date = datetime.strptime(start_datetime_str, "%A, %B %d, %Y %I:%M %p")
                
                # Парсим дату окончания, если есть
                end_date = None
                if end_time_str:
                    end_datetime_str = f"{date_str} {end_time_str}"
                    end_date = datetime.strptime(end_datetime_str, "%A, %B %d, %Y %I:%M %p")
                
                return start_date, end_date
            
            # Другие форматы даты можно добавить здесь
            
            return None, None
        except Exception as e:
            logger.error(f"Ошибка при парсинге даты '{date_text}': {str(e)}")
            return None, None