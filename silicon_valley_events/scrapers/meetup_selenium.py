import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import json

# Импортируем наш парсер
from .meetup_parser import MeetupParser

# Настройка логирования
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('meetup_selenium')

class MeetupSelenium:
    """
    Класс для загрузки страницы Meetup Events с помощью Selenium
    и последующего парсинга событий
    """
    
    def __init__(self, headless=True, timeout=None, max_pages=None):
        """
        Инициализация Selenium
        
        Args:
            headless: Запускать браузер в фоновом режиме (без GUI)
            timeout: Timeout for WebDriverWait
            max_pages: Maximum number of pages to scrape
        """
        logger.info("Инициализация Meetup Selenium")
        
        # Optional parameters for compatibility
        self.timeout = timeout
        self.max_pages = max_pages
        
        # Настройка опций Chrome
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Добавляем User-Agent для обхода блокировки ботов
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
        
        # Инициализация драйвера
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Драйвер Chrome успешно инициализирован")
        except Exception as e:
            logger.error(f"Ошибка при инициализации драйвера Chrome: {str(e)}")
            raise
        
        # Создаем директорию для сохранения HTML-страниц
        self.output_dir = os.path.join(os.getcwd(), "meetup_pages")
        if not os.path.exists(self.output_dir):
            try:
                os.makedirs(self.output_dir)
                logger.info(f"Создана директория для сохранения страниц: {self.output_dir}")
            except Exception as e:
                logger.error(f"Ошибка при создании директории: {str(e)}")
                self.output_dir = os.getcwd()
    
    def scrape_events(self):
        """
        Загрузка страницы Meetup Events и парсинг событий
        
        Returns:
            List[Event]: Список событий
        """
        try:
            # URL страницы с событиями (Кремниевая долина)
            url = "https://www.meetup.com/find/?suggested=true&source=EVENTS&location=us--ca--California%20City"
            logger.info(f"Загрузка страницы: {url}")
            
            # Загружаем страницу
            self.driver.get(url)
            
            # Ждем загрузки страницы
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Даем время для полной загрузки JavaScript-контента
            time.sleep(10)
            
            # Прокручиваем страницу вниз для загрузки всего контента
            self._scroll_to_bottom()
            
            # Сохраняем HTML-страницу
            html_content = self.driver.page_source
            main_page_path = os.path.join(self.output_dir, "meetup_main_page.html")
            with open(main_page_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"HTML-страница сохранена: {main_page_path}")
            
            # Используем наш парсер для извлечения событий
            parser = MeetupParser(html_file_path=main_page_path)
            events = parser.parse_events()
            logger.info(f"Найдено {len(events)} событий")
            
            # Для каждого события загружаем его страницу и сохраняем HTML
            # self._scrape_event_pages(events)
            
            # Сохраняем события в JSON-файл
            self._save_events_to_json(events)
            
            return events
            
        except Exception as e:
            logger.error(f"Ошибка при скрапинге событий: {str(e)}")
            return []
        finally:
            # Закрываем браузер
            self.driver.quit()
            logger.info("Браузер закрыт")
    
    def _scroll_to_bottom(self):
        """
        Прокрутка страницы вниз для загрузки всего контента
        """
        try:
            logger.info("Прокрутка страницы вниз")
            
            # Получаем высоту страницы
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Счетчик для ограничения прокрутки
            scroll_count = 0
            max_scrolls = 10  # Ограничиваем количество прокруток
            
            while scroll_count < max_scrolls:
                # Прокручиваем вниз
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Ждем загрузки контента
                time.sleep(3)
                
                # Вычисляем новую высоту страницы
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                
                # Если высота не изменилась, значит достигли конца страницы
                if new_height == last_height:
                    break
                
                last_height = new_height
                scroll_count += 1
            
            logger.info(f"Прокрутка страницы завершена после {scroll_count} прокруток")
        except Exception as e:
            logger.error(f"Ошибка при прокрутке страницы: {str(e)}")
    
    def _scrape_event_pages(self, events):
        """
        Загрузка и сохранение страниц отдельных событий
        
        Args:
            events: Список событий
        """
        try:
            logger.info("Загрузка страниц отдельных событий")
            
            # Создаем директорию для страниц событий
            events_pages_dir = os.path.join(self.output_dir, "event_pages")
            if not os.path.exists(events_pages_dir):
                os.makedirs(events_pages_dir)
            
            # Загружаем страницу каждого события
            for i, event in enumerate(events, 1):
                if not event.url:
                    logger.warning(f"Событие {i} не имеет URL, пропускаем")
                    continue
                
                try:
                    logger.info(f"Загрузка страницы события {i}: {event.url}")
                    
                    # Загружаем страницу события
                    self.driver.get(event.url)
                    
                    # Ждем загрузки страницы
                    WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    
                    # Даем время для полной загрузки JavaScript-контента
                    time.sleep(5)
                    
                    # Сохраняем HTML-страницу
                    html_content = self.driver.page_source
                    event_page_path = os.path.join(events_pages_dir, f"meetup_event_{i}.html")
                    with open(event_page_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    logger.info(f"HTML-страница события сохранена: {event_page_path}")
                    
                    # Обновляем информацию о событии из страницы события
                    parser = MeetupParser(html_file_path=event_page_path)
                    parser.update_event_details(event)
                    
                except Exception as e:
                    logger.error(f"Ошибка при загрузке страницы события {i}: {str(e)}")
                    continue
            
            logger.info("Загрузка страниц событий завершена")
        except Exception as e:
            logger.error(f"Ошибка при загрузке страниц событий: {str(e)}")
    
    def _save_events_to_json(self, events):
        """
        Сохранение списка событий в JSON-файл
        
        Args:
            events: Список событий
        """
        try:
            # Преобразуем события в словари
            events_data = []
            for event in events:
                event_dict = {
                    'id': event.id,
                    'title': event.title,
                    'description': event.description,
                    'start_date': event.start_date.isoformat() if event.start_date else None,
                    'end_date': event.end_date.isoformat() if event.end_date else None,
                    'location': event.location,
                    'url': event.url,
                    'image_url': event.image_url,
                    'source': event.source
                }
                events_data.append(event_dict)
            
            # Сохраняем в JSON-файл
            json_path = os.path.join(self.output_dir, "meetup_events.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(events_data, f, ensure_ascii=False, indent=4)
            
            logger.info(f"События сохранены в JSON-файл: {json_path}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении событий в JSON: {str(e)}")