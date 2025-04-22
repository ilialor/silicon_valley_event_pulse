import os
import re
import logging
import traceback
from bs4 import BeautifulSoup
from datetime import datetime
import dateutil.parser
from ..models.event import Event

# Настройка логирования
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('eventbrite_parser')

class EventbriteParser:
    """
    Класс для парсинга событий с Eventbrite из сохраненных HTML-страниц
    """
    
    def __init__(self):
        """
        Инициализация парсера
        """
        logger.info("Инициализация Eventbrite Parser")
        
        # Создаем директории для сохранения данных
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        self.eventbrite_dir = os.path.join(self.data_dir, 'eventbrite')
        self.events_pages_dir = os.path.join(self.eventbrite_dir, 'events_pages')
        
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.eventbrite_dir, exist_ok=True)
        os.makedirs(self.events_pages_dir, exist_ok=True)
        
        logger.info(f"Директории для данных: {self.eventbrite_dir}")
    
    def _parse_date(self, date_str):
        """
        Парсинг строки с датой в объект datetime
        
        Args:
            date_str: Строка с датой
        
        Returns:
            datetime: Объект datetime или None, если не удалось распарсить
        """
        if not date_str or date_str == 'Дата не указана':
            return None
        
        try:
            # Пробуем разные форматы даты
            return dateutil.parser.parse(date_str)
        except Exception as e:
            logger.error(f"Ошибка при парсинге даты '{date_str}': {str(e)}")
            return None
    
    def parse_events(self):
        """
        Парсинг всех сохраненных страниц событий
        
        Returns:
            List[Event]: Список событий
        """
        events = []
        
        # Получаем список всех HTML-файлов событий
        event_files = [f for f in os.listdir(self.events_pages_dir) if f.startswith('event_') and f.endswith('.html')]
        logger.info(f"Найдено {len(event_files)} HTML-файлов событий для парсинга")
        
        for event_file in event_files:
            try:
                file_path = os.path.join(self.events_pages_dir, event_file)
                logger.info(f"Парсинг файла: {file_path}")
                
                # Читаем HTML-файл
                with open(file_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # Парсим событие
                event = self._parse_event_page(html_content, file_path)
                if event:
                    events.append(event)
                    logger.info(f"Успешно распарсено событие: {event.title}")
                
            except Exception as e:
                logger.error(f"Ошибка при парсинге файла {event_file}: {str(e)}")
                logger.error(traceback.format_exc())
        
        logger.info(f"Всего успешно распарсено {len(events)} событий")
        return events
    
    def _parse_event_page(self, html_content, file_path):
        """
        Парсинг страницы события
        
        Args:
            html_content: HTML-содержимое страницы
            file_path: Путь к файлу (для логирования)
        
        Returns:
            Event: Объект события или None, если не удалось распарсить
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Извлекаем заголовок
            title = None
            title_elem = soup.select_one('h1.event-title')
            if title_elem:
                title = title_elem.text.strip()
            else:
                # Пробуем альтернативные селекторы
                title_selectors = [
                    'h1.eds-text-hl',
                    '.event-title',
                    'h1[data-automation="listing-title"]'
                ]
                for selector in title_selectors:
                    title_elem = soup.select_one(selector)
                    if title_elem:
                        title = title_elem.text.strip()
                        break
            
            if not title:
                logger.warning(f"Не удалось извлечь заголовок из {file_path}")
                return None
            
            logger.info(f"Найден заголовок: {title}")
            
            # Извлекаем URL
            url = ''
            canonical_link = soup.select_one('link[rel="canonical"]')
            if canonical_link:
                url = canonical_link.get('href', '')
            
            # Извлекаем дату
            date_str = 'Дата не указана'
            date_selectors = [
                '.date-info',
                '.eds-event-details__data-content',
                'time',
                '[data-automation="event-details-time"]'
            ]
            
            for selector in date_selectors:
                date_elem = soup.select_one(selector)
                if date_elem:
                    date_str = date_elem.text.strip()
                    logger.info(f"Найдена дата: {date_str}")
                    break
            
            # Если не нашли дату по селекторам, ищем в тексте
            if date_str == 'Дата не указана':
                text = soup.get_text()
                date_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}', text)
                if date_match:
                    date_str = date_match.group(0)
                    logger.info(f"Найдена дата в тексте: {date_str}")
            
            # Обработка диапазона дат
            start_date = None
            end_date = None
            if '–' in date_str or '-' in date_str:
                # Заменяем тире на стандартное
                date_str_normalized = date_str.replace('–', '-')
                
                # Разбиваем на части
                parts = date_str_normalized.split('-')
                if len(parts) == 2:
                    start_part = parts[0].strip()
                    end_part = parts[1].strip()
                    
                    # Извлекаем месяц из начальной части
                    month_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
                    month_match = re.search(month_pattern, start_part, re.IGNORECASE)
                    month = month_match.group(0) if month_match else None
                    
                    # Извлекаем год из конечной части
                    year_match = re.search(r'\d{4}', end_part)
                    if not year_match:
                        year_match = re.search(r'\d{4}', start_part)
                    year = year_match.group(0) if year_match else str(datetime.now().year)
                    
                    # Извлекаем день из начальной части (1-2 цифры после месяца)
                    if month:
                        day_match = re.search(fr'{month}\s+(\d{{1,2}})', start_part, re.IGNORECASE)
                        start_day = day_match.group(1) if day_match else '1'
                        
                        # Формируем полную дату начала
                        start_date_str = f"{month} {start_day}, {year}"
                        start_date = self._parse_date(start_date_str)
                        logger.info(f"Сформирована дата начала: {start_date_str}")
                    else:
                        # Если не нашли месяц, пробуем парсить как есть
                        start_date = self._parse_date(start_part)
                    
                    # Извлекаем день из конечной части (1-2 цифры до запятой или пробела)
                    end_day_match = re.search(r'(\d{1,2})(?:,|\s|$)', end_part)
                    if end_day_match and month:
                        end_day = end_day_match.group(1)
                        
                        # Формируем полную дату окончания
                        end_date_str = f"{month} {end_day}, {year}"
                        end_date = self._parse_date(end_date_str)
                        logger.info(f"Сформирована дата окончания: {end_date_str}")
                    else:
                        # Если не нашли день, пробуем парсить как есть
                        end_date = self._parse_date(end_part)
                    
                    logger.info(f"Обработка диапазона: Начало='{start_date}', Конец='{end_date}'")
                else:
                    # Если не удалось разбить на части, пробуем парсить как одну дату
                    start_date = self._parse_date(date_str)
            else:
                # Если это не диапазон, просто парсим дату
                start_date = self._parse_date(date_str)
            
            # Извлекаем локацию
            location = 'Место не указано'
            location_selectors = [
                '.location-info',
                '.eds-event-details__data-content--location',
                '[data-automation="event-details-location"]'
            ]
            
            for selector in location_selectors:
                location_elem = soup.select_one(selector)
                if location_elem:
                    location = location_elem.text.strip()
                    logger.info(f"Найдена локация: {location}")
                    break
            
            # Извлекаем URL изображения
            image_url = ''
            image_selectors = [
                'meta[property="og:image"]',
                'meta[name="twitter:image"]',
                '.event-header__image img',
                '.listing-hero img'
            ]
            
            for selector in image_selectors:
                image_elem = soup.select_one(selector)
                if image_elem:
                    if selector.endswith('img'):
                        image_url = image_elem.get('src', '')
                    else:
                        image_url = image_elem.get('content', '')
                    
                    if image_url:
                        logger.info(f"Найдено изображение: {image_url}")
                        break
            
            # Создаем объект события
            event = Event(
                title=title,
                start_date=start_date,
                end_date=end_date,
                location=location,
                url=url,
                image_url=image_url,
                source="Eventbrite"
            )
            
            return event
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге страницы события: {str(e)}")
            logger.error(traceback.format_exc())
            return None

# Точка входа для запуска модуля напрямую
if __name__ == "__main__":
    parser = EventbriteParser()
    events = parser.parse_events()
    
    print(f"Найдено событий: {len(events)}")
    for event in events:
        print(f"- {event.title} ({event.start_date})")