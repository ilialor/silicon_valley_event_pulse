import logging
import os
import re
import uuid
import traceback
import json  # Добавляем импорт модуля json
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
logger = logging.getLogger('techcrunch_parser')

class TechCrunchParser:
    """
    Парсер для извлечения событий из сохраненной HTML-страницы TechCrunch Events
    """
    
    def __init__(self, html_file_path=None):
        """
        Инициализация парсера
        
        Args:
            html_file_path: Путь к сохраненному HTML-файлу
        """
        self.html_file_path = html_file_path or os.path.join(os.getcwd(), "techcrunch_main_page.html")
        logger.info(f"Инициализация парсера TechCrunch с файлом: {self.html_file_path}")
        
        # Создаем папку для сохранения страниц событий
        self.events_pages_dir = os.path.join(os.getcwd(), "techcrunch_events_pages")
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
                            source="TechCrunch Events (JSON-LD)"
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
            
            # Пробуем различные селекторы для поиска событий
            selectors = [
                '.wp-block-post.tc_event',
                '.loop-card',
                '.wp-block-techcrunch-card',
                'article.post',
                '.wp-block-post',
                '.event-card',
                '.event-listing'
            ]
            
            event_cards = []
            for selector in selectors:
                cards = soup.select(selector)
                logger.info(f"Селектор '{selector}': найдено {len(cards)} элементов")
                if cards:
                    event_cards = cards
                    logger.info(f"Используем селектор '{selector}' для парсинга событий")
                    break
            
            if not event_cards:
                # Если не нашли по селекторам, попробуем найти по ключевым словам
                logger.info("Поиск событий по ключевым словам в тексте")
                potential_events = []
                
                # Ищем все ссылки, которые могут вести на страницы событий
                links = soup.find_all('a')
                for link in links:
                    href = link.get('href', '')
                    text = link.get_text().strip()
                    
                    # Проверяем, похоже ли это на событие
                    if ('event' in href.lower() or 
                        'conference' in href.lower() or 
                        'summit' in href.lower() or
                        'disrupt' in href.lower()):
                        logger.info(f"Найдена потенциальная ссылка на событие: {text} - {href}")
                        parent = link.parent
                        potential_events.append((parent, href, text))
                
                logger.info(f"Найдено {len(potential_events)} потенциальных событий по ключевым словам")
                
                # Используем найденные потенциальные события
                events = []
                for i, (element, url, title) in enumerate(potential_events, 1):
                    try:
                        logger.info(f"Обработка потенциального события {i}/{len(potential_events)}: {title}")
                        
                        # Ищем дату и место в тексте вокруг ссылки
                        surrounding_text = element.get_text()
                        
                        # Сохраняем HTML элемента для отладки
                        event_debug_path = os.path.join(self.events_pages_dir, f"potential_event_{i}.html")
                        with open(event_debug_path, 'w', encoding='utf-8') as f:
                            f.write(str(element))
                        logger.info(f"Сохранен HTML потенциального события для отладки: {event_debug_path}")
                        
                        # Ищем дату в тексте
                        date_match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}', surrounding_text)
                        date_str = date_match.group(0) if date_match else 'Дата не указана'
                        
                        # Ищем место проведения
                        location = 'Место не указано'
                        location_patterns = ['in ', 'at ', 'location: ', 'venue: ']
                        for pattern in location_patterns:
                            if pattern in surrounding_text.lower():
                                location_text = surrounding_text.lower().split(pattern)[1].split('\n')[0].strip()
                                if location_text:
                                    location = location_text
                                    break
                        
                        # Ищем изображение
                        image_url = ''
                        img_tag = element.find('img')
                        if img_tag:
                            image_url = img_tag.get('src', '')
                        
                        # Создаем объект события
                        event = Event(
                            title=title,
                            description=surrounding_text[:200] + "..." if len(surrounding_text) > 200 else surrounding_text,
                            start_date=self._parse_date(date_str),
                            end_date=None,
                            location=location,
                            url=url,
                            image_url=image_url,
                            source="TechCrunch Events (по ключевым словам)"
                        )
                        
                        events.append(event)
                        logger.info(f"Событие успешно обработано: {title}")
                        
                    except Exception as e:
                        logger.error(f"Ошибка при обработке потенциального события {i}: {str(e)}")
                        logger.error(traceback.format_exc())
                        continue
                
                logger.info(f"Всего успешно обработано {len(events)} потенциальных событий")
                return events
            
            # Парсинг информации о каждом событии
            events = []
            for i, card in enumerate(event_cards, 1):
                try:
                    logger.info(f"Обработка события {i}/{len(event_cards)}")
                    
                    # Сохраняем HTML карточки для отладки
                    card_debug_path = os.path.join(self.events_pages_dir, f"event_card_{i}.html")
                    with open(card_debug_path, 'w', encoding='utf-8') as f:
                        f.write(str(card))
                    logger.info(f"Сохранен HTML карточки события для отладки: {card_debug_path}")
                    
                    # Получаем контейнер карточки
                    loop_card = card
                    
                    # Пробуем различные селекторы для извлечения данных
                    title = None
                    url = None
                    date_str = 'Дата не указана'
                    location = 'Место не указано'
                    image_url = ''
                    
                    # Извлекаем заголовок и URL
                    title_selectors = [
                        '.loop-card__title-link', 
                        'h2 a', 
                        'h3 a', 
                        '.event-title a', 
                        'a.title',
                        '.wp-block-post-title a'
                    ]
                    
                    for selector in title_selectors:
                        title_link = loop_card.select_one(selector)
                        if title_link:
                            title = title_link.text.strip()
                            url = title_link.get('href', '')
                            logger.info(f"Найден заголовок по селектору '{selector}': {title}")
                            break
                    
                    # Если не нашли по селекторам, ищем любую ссылку
                    if not title:
                        any_link = loop_card.find('a')
                        if any_link:
                            title = any_link.text.strip() or any_link.get('title', 'Нет названия')
                            url = any_link.get('href', '')
                            logger.info(f"Найден заголовок по тегу 'a': {title}")
                    
                    # Извлекаем дату
                    date_selectors = [
                        '.loop-card__meta-item.loop-card__date',
                        '.event-date',
                        '.date',
                        'time',
                        '.meta-date'
                    ]
                    
                    for selector in date_selectors:
                        date_elem = loop_card.select_one(selector)
                        if date_elem:
                            date_str = date_elem.text.strip()
                            logger.info(f"Найдена дата по селектору '{selector}': {date_str}")
                            break
                    
                    # Если не нашли дату по селекторам, ищем в тексте
                    if date_str == 'Дата не указана':
                        text = loop_card.get_text()
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
                    
                    # Извлекаем место проведения
                    location_selectors = [
                        '.loop-card__meta-item.loop-card__location',
                        '.event-location',
                        '.location',
                        '.venue'
                    ]
                    
                    for selector in location_selectors:
                        location_elem = loop_card.select_one(selector)
                        if location_elem:
                            location = location_elem.text.strip()
                            logger.info(f"Найдено место по селектору '{selector}': {location}")
                            break
                    
                    # Если не нашли место по селекторам, ищем в тексте
                    if location == 'Место не указано':
                        text = loop_card.get_text()
                        location_patterns = ['in ', 'at ', 'location: ', 'venue: ']
                        for pattern in location_patterns:
                            if pattern in text.lower():
                                location_text = text.lower().split(pattern)[1].split('\n')[0].strip()
                                if location_text:
                                    location = location_text
                                    logger.info(f"Найдено место в тексте: {location}")
                                    break
                    
                    # Извлекаем изображение
                    image_selectors = [
                        '.loop-card__figure img',
                        '.event-image img',
                        '.featured-image img',
                        'img.wp-post-image'
                    ]
                    
                    for selector in image_selectors:
                        img = loop_card.select_one(selector)
                        if img:
                            image_url = img.get('src', '')
                            logger.info(f"Найдено изображение по селектору '{selector}': {image_url}")
                            break
                    
                    # Создаем объект события
                    event = Event(
                        title=title,
                        description="",  # Описание отсутствует на главной странице
                        start_date=self._parse_date(date_str),
                        end_date=None,  # Конечная дата отсутствует
                        location=location,
                        url=url,
                        image_url=image_url,
                        source="TechCrunch Events"
                    )
                    
                    events.append(event)
                    logger.info(f"Событие успешно обработано: {title}")
                    
                except Exception as e:
                    logger.error(f"Ошибка при обработке события {i}: {str(e)}")
                    logger.error(traceback.format_exc())
                    continue
            
            logger.info(f"Всего успешно обработано {len(events)} событий")
            return events
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге событий: {str(e)}")
            logger.error(traceback.format_exc())
            return []
    
    def _parse_date(self, date_str):
        """
        Парсинг даты из строки в объект datetime
        
        Args:
            date_str: Строка с датой
            
        Returns:
            datetime: Объект даты или None, если не удалось распарсить
        """
        if not date_str or date_str == 'Дата не указана':
            return None
        
        # Нормализуем строку даты
        date_str = date_str.strip()
        
        # Список форматов для парсинга
        formats = [
            '%B %d, %Y',  # January 1, 2025
            '%b %d, %Y',  # Jan 1, 2025
            '%d %B %Y',   # 1 January 2025
            '%d %b %Y',   # 1 Jan 2025
            '%Y-%m-%d',   # 2025-01-01
            '%m/%d/%Y',   # 01/01/2025
            '%d.%m.%Y',   # 01.01.2025
            '%B %Y',      # January 2025
            '%b %Y',      # Jan 2025
            '%B %d',      # January 1
            '%b %d'       # Jan 1
        ]
        
        # Пробуем разные форматы
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Если не удалось распарсить стандартными форматами, пробуем извлечьь части даты
        try:
            # Ищем месяц
            month_pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
            month_match = re.search(month_pattern, date_str, re.IGNORECASE)
            
            # Ищем день
            day_match = re.search(r'\b(\d{1,2})\b', date_str)
            
            # Ищем год
            year_match = re.search(r'\b(\d{4})\b', date_str)
            
            if month_match:
                month_str = month_match.group(1)
                month_map = {
                    'january': 1, 'jan': 1,
                    'february': 2, 'feb': 2,
                    'march': 3, 'mar': 3,
                    'april': 4, 'apr': 4,
                    'may': 5,
                    'june': 6, 'jun': 6,
                    'july': 7, 'jul': 7,
                    'august': 8, 'aug': 8,
                    'september': 9, 'sep': 9,
                    'october': 10, 'oct': 10,
                    'november': 11, 'nov': 11,
                    'december': 12, 'dec': 12
                }
                month = month_map.get(month_str.lower())
                
                day = int(day_match.group(1)) if day_match else 1
                year = int(year_match.group(1)) if year_match else datetime.now().year
                
                return datetime(year, month, day)
        except Exception as e:
            logger.warning(f"Не удалось распознать дату '{date_str}' ни одним из известных форматов.")
            return None
        
        logger.warning(f"Не удалось распознать дату '{date_str}' ни одним из известных форматов.")
        return None

# Добавляем точку входа для запуска модуля напрямую
if __name__ == "__main__":
    parser = TechCrunchParser()
    events = parser.parse_events()
    print(f"Найдено событий: {len(events)}")
    for event in events:
        print(f"- {event.title} ({event.start_date})")