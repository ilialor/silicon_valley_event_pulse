import scrapy
from datetime import datetime
import re
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from ..models.event import Event
from ..config.settings import USER_AGENTS
import random
import time

logger = logging.getLogger(__name__)

class BaseEventSpider(scrapy.Spider):
    """
    Базовый класс для скрейпинга событий с использованием Scrapy.
    Предоставляет общую функциональность для всех пауков событий.
    """
    name = "base_event_spider"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events = []
        self.user_agent = random.choice(USER_AGENTS)
        
    def parse(self, response):
        """
        Базовый метод парсинга, который должен быть переопределен в подклассах.
        """
        raise NotImplementedError("Subclasses must implement parse method")
    
    def extract_date(self, date_str: str) -> Optional[datetime]:
        """
        Извлекает объект datetime из строки даты.
        
        Args:
            date_str: Строка с датой в различных форматах
            
        Returns:
            datetime: Объект datetime или None, если парсинг не удался
        """
        try:
            # Попытка парсинга различных форматов даты
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%Y-%m-%d",
                "%d.%m.%Y %H:%M",
                "%d.%m.%Y",
                "%B %d, %Y %I:%M %p",
                "%B %d, %Y",
                "%a, %b %d, %Y %I:%M %p",
                "%a, %b %d, %Y"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str.strip(), fmt)
                except ValueError:
                    continue
                    
            # Если стандартные форматы не подошли, пробуем регулярные выражения
            # Формат: "May 15, 2023" или "May 15"
            month_day_pattern = r'(\w+)\s+(\d{1,2})(?:,\s+(\d{4}))?'
            match = re.search(month_day_pattern, date_str)
            if match:
                month, day = match.groups()[0:2]
                year = match.groups()[2] if match.groups()[2] else datetime.now().year
                month_num = {
                    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                }.get(month.lower()[0:3], 1)
                
                return datetime(int(year), month_num, int(day))
                
            logger.warning(f"Не удалось распознать формат даты: {date_str}")
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении даты из {date_str}: {str(e)}")
            return None
    
    def clean_text(self, text: str) -> str:
        """
        Очищает текст от лишних пробелов и HTML-тегов.
        
        Args:
            text: Исходный текст
            
        Returns:
            str: Очищенный текст
        """
        if not text:
            return ""
            
        # Удаление HTML-тегов
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # Замена множественных пробелов, табуляций и переносов строк на один пробел
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def create_event(self, **kwargs) -> Event:
        """
        Создает объект события из извлеченных данных.
        
        Args:
            **kwargs: Параметры события (title, description, start_date и т.д.)
            
        Returns:
            Event: Объект события
        """
        try:
            # Создание события с обязательными полями
            event = Event(
                title=kwargs.get('title', ''),
                description=kwargs.get('description', ''),
                start_date=kwargs.get('start_date'),
                end_date=kwargs.get('end_date'),
                location=kwargs.get('location', ''),
                url=kwargs.get('url', ''),
                source=self.name,
                tags=kwargs.get('tags', []),
                image_url=kwargs.get('image_url', ''),
                organizer=kwargs.get('organizer', ''),
                price=kwargs.get('price', ''),
                is_online=kwargs.get('is_online', False)
            )
            
            self.events.append(event)
            return event
            
        except Exception as e:
            logger.error(f"Ошибка при создании события: {str(e)}")
            return None
    
    def closed(self, reason):
        """
        Вызывается при завершении работы паука.
        
        Args:
            reason: Причина завершения
        """
        logger.info(f"Паук {self.name} завершил работу. Причина: {reason}")
        logger.info(f"Собрано событий: {len(self.events)}")


class SeleniumEventScraper(ABC):
    """
    Базовый класс для скрейпинга событий с использованием Selenium.
    Используется для сайтов, требующих JavaScript или взаимодействия с пользователем.
    """
    
    def __init__(self, headless: bool = True):
        """
        Инициализирует скрейпер Selenium.
        
        Args:
            headless: Запускать браузер в фоновом режиме без GUI
        """
        self.events = []
        self.driver = None
        self.headless = headless
        
    def setup_driver(self):
        """
        Настраивает и инициализирует драйвер Selenium.
        """
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")
            
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(10)
            
            logger.info("Драйвер Selenium успешно инициализирован")
            
        except Exception as e:
            logger.error(f"Ошибка при инициализации драйвера Selenium: {str(e)}")
            raise
    
    def close(self):
        """
        Закрывает драйвер Selenium.
        """
        if self.driver:
            self.driver.quit()
            logger.info("Драйвер Selenium закрыт")
    
    @abstractmethod
    async def fetch_events(self, start_date: datetime, end_date: datetime) -> List[Event]:
        """
        Извлекает события в указанном диапазоне дат.
        
        Args:
            start_date: Начальная дата
            end_date: Конечная дата
            
        Returns:
            List[Event]: Список событий
        """
        pass
    
    def extract_date(self, date_str: str) -> Optional[datetime]:
        """
        Извлекает объект datetime из строки даты.
        
        Args:
            date_str: Строка с датой в различных форматах
            
        Returns:
            datetime: Объект datetime или None, если парсинг не удался
        """
        try:
            # Попытка парсинга различных форматов даты
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%Y-%m-%d",
                "%d.%m.%Y %H:%M",
                "%d.%m.%Y",
                "%B %d, %Y %I:%M %p",
                "%B %d, %Y",
                "%a, %b %d, %Y %I:%M %p",
                "%a, %b %d, %Y"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str.strip(), fmt)
                except ValueError:
                    continue
                    
            # Если стандартные форматы не подошли, пробуем регулярные выражения
            # Формат: "May 15, 2023" или "May 15"
            month_day_pattern = r'(\w+)\s+(\d{1,2})(?:,\s+(\d{4}))?'
            match = re.search(month_day_pattern, date_str)
            if match:
                month, day = match.groups()[0:2]
                year = match.groups()[2] if match.groups()[2] else datetime.now().year
                month_num = {
                    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                }.get(month.lower()[0:3], 1)
                
                return datetime(int(year), month_num, int(day))
                
            logger.warning(f"Не удалось распознать формат даты: {date_str}")
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении даты из {date_str}: {str(e)}")
            return None
    
    def clean_text(self, text: str) -> str:
        """
        Очищает текст от лишних пробелов и HTML-тегов.
        
        Args:
            text: Исходный текст
            
        Returns:
            str: Очищенный текст
        """
        if not text:
            return ""
            
        # Удаление HTML-тегов
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # Замена множественных пробелов, табуляций и переносов строк на один пробел
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def create_event(self, **kwargs) -> Event:
        """
        Создает объект события из извлеченных данных.
        
        Args:
            **kwargs: Параметры события (title, description, start_date и т.д.)
            
        Returns:
            Event: Объект события
        """
        try:
            # Создание события с обязательными полями
            event = Event(
                title=kwargs.get('title', ''),
                description=kwargs.get('description', ''),
                start_date=kwargs.get('start_date'),
                end_date=kwargs.get('end_date'),
                location=kwargs.get('location', ''),
                url=kwargs.get('url', ''),
                source=self.__class__.__name__,
                tags=kwargs.get('tags', []),
                image_url=kwargs.get('image_url', ''),
                organizer=kwargs.get('organizer', ''),
                price=kwargs.get('price', ''),
                is_online=kwargs.get('is_online', False)
            )
            
            self.events.append(event)
            return event
            
        except Exception as e:
            logger.error(f"Ошибка при создании события: {str(e)}")
            return None
    
    def scroll_to_bottom(self, scroll_pause_time: float = 1.0, max_scrolls: int = 10):
        """
        Прокручивает страницу до конца для загрузки динамического контента.
        
        Args:
            scroll_pause_time: Время паузы между прокрутками (в секундах)
            max_scrolls: Максимальное количество прокруток
        """
        try:
            # Получаем начальную высоту прокрутки
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            scrolls = 0
            while scrolls < max_scrolls:
                # Прокручиваем вниз
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Ждем загрузки страницы
                time.sleep(scroll_pause_time)
                
                # Вычисляем новую высоту прокрутки и сравниваем с последней
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                scrolls += 1
                
        except Exception as e:
            logger.error(f"Ошибка при прокрутке страницы: {str(e)}")