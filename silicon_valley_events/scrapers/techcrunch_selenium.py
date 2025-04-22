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
from .techcrunch_parser import TechCrunchParser

# Настройка логирования
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('techcrunch_selenium')

class TechCrunchSelenium:
    """
    Класс для загрузки страницы TechCrunch Events с помощью Selenium
    и последующего парсинга событий
    """
    
    def __init__(self, headless=True, timeout=None, max_pages=None):
        """
        Инициализация Selenium
        
        Args:
            headless: Запускать браузер в фоновом режиме (без GUI)
            timeout: WebDriver wait timeout (seconds)
            max_pages: Maximum number of pages to scrape
        """
        logger.info("Инициализация TechCrunch Selenium")
        
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
        
        # Инициализация драйвера
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Драйвер Chrome успешно инициализирован")
        except Exception as e:
            logger.error(f"Ошибка при инициализации драйвера Chrome: {str(e)}")
            raise
        
        # Создаем директорию для сохранения HTML-страниц
        self.output_dir = os.path.join(os.getcwd(), "techcrunch_pages")
        if not os.path.exists(self.output_dir):
            try:
                os.makedirs(self.output_dir)
                logger.info(f"Создана директория для сохранения страниц: {self.output_dir}")
            except Exception as e:
                logger.error(f"Ошибка при создании директории: {str(e)}")
                self.output_dir = os.getcwd()
    
    def scrape_events(self):
        """
        Загрузка страницы TechCrunch Events и парсинг событий
        
        Returns:
            List[Event]: Список событий
        """
        try:
            # URL страницы с событиями
            url = "https://techcrunch.com/events/"
            logger.info(f"Загрузка страницы: {url}")
            
            # Загружаем страницу
            self.driver.get(url)
            
            # Ждем загрузки страницы
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Даем время для полной загрузки JavaScript-контента
            time.sleep(5)
            
            # Прокручиваем страницу вниз для загрузки всего контента
            self._scroll_to_bottom()
            
            # Сохраняем HTML-страницу
            html_content = self.driver.page_source
            main_page_path = os.path.join(self.output_dir, "techcrunch_main_page.html")
            with open(main_page_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"HTML-страница сохранена: {main_page_path}")
            
            # Используем наш парсер для извлечения событий
            parser = TechCrunchParser(html_file_path=main_page_path)
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
            
            while True:
                # Прокручиваем вниз
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Ждем загрузки контента
                time.sleep(2)
                
                # Вычисляем новую высоту страницы
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                
                # Если высота не изменилась, значит достигли конца страницы
                if new_height == last_height:
                    break
                
                last_height = new_height
            
            logger.info("Прокрутка страницы завершена")
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
                    logger.info(f"Загрузка страницы события {i}/{len(events)}: {event.title}")
                    
                    # Загружаем страницу
                    self.driver.get(event.url)
                    
                    # Ждем загрузки страницы
                    WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    
                    # Даем время для полной загрузки JavaScript-контента
                    time.sleep(3)
                    
                    # Сохраняем HTML-страницу
                    html_content = self.driver.page_source
                    
                    # Создаем безопасное имя файла из заголовка события
                    safe_title = "".join(c if c.isalnum() else "_" for c in event.title)
                    safe_title = safe_title[:50]  # Ограничиваем длину имени файла
                    
                    event_page_path = os.path.join(events_pages_dir, f"event_{i}_{safe_title}.html")
                    with open(event_page_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    logger.info(f"Страница события сохранена: {event_page_path}")
                    
                    # Добавляем путь к HTML-файлу в объект события
                    event.html_file_path = event_page_path
                    
                except Exception as e:
                    logger.error(f"Ошибка при загрузке страницы события {i}: {str(e)}")
                    continue
            
            logger.info("Загрузка страниц событий завершена")
        except Exception as e:
            logger.error(f"Ошибка при загрузке страниц событий: {str(e)}")
    
    def _save_events_to_json(self, events):
        """
        Сохранение событий в JSON-файл
        
        Args:
            events: Список событий
        """
        try:
            # Создаем список словарей из объектов событий
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
            
            # Формируем имя файла с текущей датой
            current_date = datetime.now().strftime("%Y-%m-%d")
            json_file_path = os.path.join(self.output_dir, f"techcrunch_events_{current_date}.json")
            
            # Сохраняем в JSON-файл
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(events_data, f, ensure_ascii=False, indent=4)
            
            logger.info(f"События сохранены в JSON-файл: {json_file_path}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении событий в JSON: {str(e)}")


if __name__ == "__main__":
    # Пример использования
    scraper = TechCrunchSelenium(headless=True)
    events = scraper.scrape_events()
    
    print(f"\nНайдено {len(events)} событий:")
    for i, event in enumerate(events, 1):
        print(f"\nСобытие {i}:")
        print(f"Название: {event.title}")
        print(f"Дата: {event.start_date}")
        print(f"Место: {event.location}")
        print(f"URL события: {event.url}")