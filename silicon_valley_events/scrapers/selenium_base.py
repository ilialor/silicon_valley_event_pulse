import logging
import time
from abc import ABC, abstractmethod
from typing import List, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import random  # Добавляем импорт модуля random
import time
from ..models.event import Event
from ..config.settings import USER_AGENTS
from datetime import datetime
import uuid
import re

logger = logging.getLogger(__name__)

class BaseSeleniumScraper:
    """
    Базовый класс для скрейперов на основе Selenium
    """
    
    def __init__(self, headless=True, timeout=10):
        """
        Инициализация скрейпера
        
        Args:
            headless (bool): Запускать браузер в фоновом режиме
            timeout (int): Таймаут ожидания элементов в секундах
        """
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        self.events = []
        self.event_count = 0
    
    def setup_driver(self, proxy=None):
        """
        Настройка драйвера Selenium
        
        Args:
            proxy (str): Прокси-сервер в формате 'ip:port'
        """
        options = webdriver.ChromeOptions()
        
        if self.headless:
            options.add_argument('--headless')
        
        # Добавляем прокси, если он указан
        if proxy:
            options.add_argument(f'--proxy-server={proxy}')
        
        # Другие полезные опции
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Маскируемся под обычный браузер
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Устанавливаем случайный User-Agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
        ]
        options.add_argument(f'user-agent={random.choice(user_agents)}')
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_page_load_timeout(60)  # Увеличиваем таймаут загрузки страницы
        # Добавьте в метод setup_driver
        # Устанавливаем параметры для маскировки Selenium
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            """
        })
    
    def close(self):
        """
        Закрытие драйвера
        """
        if self.driver:
            self.driver.quit()
            logger.info("Selenium WebDriver закрыт")
    
    def wait_for_element(self, by, value, timeout=None):
        """
        Ожидание появления элемента на странице
        
        Args:
            by: Метод поиска (By.ID, By.CSS_SELECTOR и т.д.)
            value: Значение для поиска
            timeout: Таймаут ожидания в секундах (если None, используется self.timeout)
        
        Returns:
            WebElement: Найденный элемент
        """
        if timeout is None:
            timeout = self.timeout
        
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            logger.warning(f"Таймаут при ожидании элемента {by}={value}")
            return None
    
    def wait_for_elements(self, by, value, timeout=None):
        """
        Ожидание появления элементов на странице
        
        Args:
            by: Метод поиска (By.ID, By.CSS_SELECTOR и т.д.)
            value: Значение для поиска
            timeout: Таймаут ожидания в секундах (если None, используется self.timeout)
        
        Returns:
            List[WebElement]: Список найденных элементов
        """
        if timeout is None:
            timeout = self.timeout
        
        try:
            elements = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_all_elements_located((by, value))
            )
            return elements
        except TimeoutException:
            logger.warning(f"Таймаут при ожидании элементов {by}={value}")
            return []
    
    def scroll_down(self, amount=None):
        """
        Прокрутка страницы вниз
        
        Args:
            amount: Количество пикселей для прокрутки (если None, прокручивает до конца страницы)
        """
        if amount:
            self.driver.execute_script(f"window.scrollBy(0, {amount});")
        else:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)  # Даем время для загрузки контента
    
    def clean_text(self, text):
        """
        Очистка текста от лишних пробелов и переносов строк
        
        Args:
            text: Исходный текст
        
        Returns:
            str: Очищенный текст
        """
        if not text:
            return ""
        
        # Заменяем множественные пробелы и переносы строк на один пробел
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def extract_date(self, date_str):
        """
        Извлечение даты из строки
        
        Args:
            date_str: Строка с датой
        
        Returns:
            datetime: Объект даты и времени
        """
        try:
            # Здесь можно добавить различные форматы дат
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%Y-%m-%d",
                "%d.%m.%Y %H:%M",
                "%d.%m.%Y",
                "%B %d, %Y",
                "%b %d, %Y",
                "%d %B %Y",
                "%d %b %Y"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str.strip(), fmt)
                except ValueError:
                    continue
            
            # Если не удалось распознать дату, возвращаем текущую
            logger.warning(f"Не удалось распознать дату: {date_str}")
            return datetime.now()
        except Exception as e:
            logger.error(f"Ошибка при извлечении даты: {str(e)}")
            return datetime.now()
    
    def create_event(self, title, description, start_time, location, url, source, tags=None, image_url=None, organizer=None, is_online=False, end_time=None):
        """
        Создание объекта события
        
        Args:
            title: Название события
            description: Описание события
            start_time: Время начала
            location: Местоположение
            url: URL события
            source: Источник события
            tags: Теги события
            image_url: URL изображения
            organizer: Организатор
            is_online: Является ли событие онлайн
            end_time: Время окончания
        
        Returns:
            Event: Объект события
        """
        event_id = str(uuid.uuid4())
        
        if tags is None:
            tags = []
        
        # Добавляем стандартный тег для источника
        if source.lower() not in [t.lower() for t in tags]:
            tags.append(source.lower())
        
        event = Event(
            id=event_id,
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            location=location,
            url=url,
            source=source,
            tags=tags,
            image_url=image_url,
            organizer=organizer,
            is_online=is_online
        )
        
        self.events.append(event)
        self.event_count += 1
        
        logger.info(f"Создано событие {source}: {title}")
        return event

    def solve_captcha(self, iframe_selector):
        """
        Обработка CAPTCHA на странице
        
        Args:
            iframe_selector (str): CSS-селектор iframe с капчей
        """
        try:
            # Переключаемся на iframe с капчей
            captcha_iframe = self.driver.find_element(By.CSS_SELECTOR, iframe_selector)
            self.driver.switch_to.frame(captcha_iframe)
            
            # Находим и кликаем на чекбокс "Я не робот"
            checkbox = self.driver.find_element(By.CSS_SELECTOR, ".recaptcha-checkbox-border")
            checkbox.click()
            
            # Возвращаемся к основному содержимому
            self.driver.switch_to.default_content()
            
            # Ждем некоторое время для проверки
            time.sleep(5)
            
            return True
        except Exception as e:
            logger.error(f"Ошибка при решении капчи: {str(e)}")