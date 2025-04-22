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
from .eventbrite_parser import EventbriteParser

# Настройка логирования
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('eventbrite_selenium')

class EventbriteSelenium:
    """
    Класс для загрузки страницы Eventbrite Events с помощью Selenium
    и последующего парсинга событий
    """
    
    def __init__(self, headless=True):
        """
        Инициализация Selenium
        
        Args:
            headless: Запускать браузер в фоновом режиме (без GUI)
        """
        logger.info("Инициализация Eventbrite Selenium")
        
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
        
        # Создаем директории для сохранения данных
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        self.eventbrite_dir = os.path.join(self.data_dir, 'eventbrite')
        self.events_pages_dir = os.path.join(self.eventbrite_dir, 'events_pages')
        
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.eventbrite_dir, exist_ok=True)
        os.makedirs(self.events_pages_dir, exist_ok=True)
        
        logger.info(f"Созданы директории для сохранения данных: {self.eventbrite_dir}")
    
    def __del__(self):
        """
        Закрытие драйвера при уничтожении объекта
        """
        if hasattr(self, 'driver'):
            try:
                self.driver.quit()
                logger.info("Драйвер Chrome успешно закрыт")
            except Exception as e:
                logger.error(f"Ошибка при закрытии драйвера Chrome: {str(e)}")
    
    def search_events(self, keywords, location="San Francisco, CA", max_pages=5):
        """
        Поиск событий на Eventbrite по ключевым словам и локации
        
        Args:
            keywords: Список ключевых слов для поиска
            location: Локация для поиска (по умолчанию "San Francisco, CA")
            max_pages: Максимальное количество страниц для парсинга
        
        Returns:
            List[Event]: Список найденных событий
        """
        all_events = []
        
        for keyword in keywords:
            logger.info(f"Поиск событий по ключевому слову: '{keyword}' в локации '{location}'")
            
            # Build search URL based on location (City, State) and keyword
            if ',' in location:
                city, state = location.split(',')
                state_slug = state.strip().lower()
                city_slug = city.strip().lower().replace(' ', '-')
                location_slug = f"{state_slug}--{city_slug}"
            else:
                location_slug = location.strip().lower().replace(' ', '-')
            keyword_slug = keyword.strip().lower().replace(' ', '-')
            # Start from page 1
            search_url = f"https://www.eventbrite.com"
            # search_url = f"https://www.eventbrite.com/d/{location_slug}/{keyword_slug}/?page=1"
            
            try:
                # Navigate to homepage first to avoid captcha
                try:
                    self.driver.get("https://www.eventbrite.com")
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    homepage_path = os.path.join(
                        self.eventbrite_dir,
                        f"homepage_{keyword.replace(' ', '_')}.html"
                    )
                    with open(homepage_path, 'w', encoding='utf-8') as f:
                        f.write(self.driver.page_source)
                    logger.info(f"Saved Eventbrite homepage: {homepage_path}")
                except Exception as e:
                    logger.error(f"Error loading Eventbrite homepage: {str(e)}")
                # Загружаем страницу поиска
                self.driver.get(search_url)
                logger.info(f"Загружена страница поиска: {search_url}")
                                
                # Ждем загрузки результатов
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".search-results-container"))
                )
                
                # Сохраняем HTML страницы поиска
                search_page_path = os.path.join(self.eventbrite_dir, f"search_{keyword.replace(' ', '_')}.html")
                with open(search_page_path, 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                logger.info(f"Сохранена страница поиска: {search_page_path}")
                
                # Парсим события с первой страницы
                events = self._parse_search_page(keyword)
                all_events.extend(events)
                
                # Переходим на следующие страницы, если нужно
                current_page = 1
                while current_page < max_pages:
                    try:
                        # Проверяем наличие кнопки "Следующая страница"
                        next_button = self.driver.find_element(By.CSS_SELECTOR, "button[data-spec='page-next']")
                        
                        if not next_button.is_enabled():
                            logger.info("Достигнут конец результатов поиска")
                            break
                        
                        # Переходим на следующую страницу
                        next_button.click()
                        current_page += 1
                        logger.info(f"Переход на страницу {current_page}")
                        
                        # Ждем загрузки результатов
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".search-results-container"))
                        )
                        
                        # Сохраняем HTML страницы поиска
                        search_page_path = os.path.join(self.eventbrite_dir, f"search_{keyword.replace(' ', '_')}_page{current_page}.html")
                        with open(search_page_path, 'w', encoding='utf-8') as f:
                            f.write(self.driver.page_source)
                        logger.info(f"Сохранена страница поиска: {search_page_path}")
                        
                        # Парсим события с текущей страницы
                        events = self._parse_search_page(keyword)
                        all_events.extend(events)
                        
                    except Exception as e:
                        logger.error(f"Ошибка при переходе на следующую страницу: {str(e)}")
                        break
            
            except Exception as e:
                logger.error(f"Ошибка при загрузке страницы поиска: {str(e)}")
                continue
        
        logger.info(f"Всего найдено {len(all_events)} событий")
        return all_events
    
    def _parse_search_page(self, keyword):
        """
        Парсинг страницы с результатами поиска
        
        Args:
            keyword: Ключевое слово, по которому производился поиск
        
        Returns:
            List[Event]: Список событий с текущей страницы
        """
        events = []
        
        try:
            # Находим все карточки событий
            event_cards = self.driver.find_elements(By.CSS_SELECTOR, ".search-event-card-wrapper")
            logger.info(f"Найдено {len(event_cards)} карточек событий на текущей странице")
            
            # Обрабатываем каждую карточку
            for i, card in enumerate(event_cards, 1):
                try:
                    # Получаем ссылку на событие
                    event_link = card.find_element(By.CSS_SELECTOR, "a.event-card-link").get_attribute("href")
                    
                    # Сохраняем HTML карточки для отладки
                    card_html = card.get_attribute("outerHTML")
                    card_debug_path = os.path.join(self.events_pages_dir, f"event_card_{keyword.replace(' ', '_')}_{i}.html")
                    with open(card_debug_path, 'w', encoding='utf-8') as f:
                        f.write(card_html)
                    logger.info(f"Сохранен HTML карточки события для отладки: {card_debug_path}")
                    
                    # Загружаем страницу события
                    self.driver.execute_script("window.open('');")
                    self.driver.switch_to.window(self.driver.window_handles[1])
                    self.driver.get(event_link)
                    logger.info(f"Загружена страница события: {event_link}")
                    
                    # Ждем загрузки страницы события
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "main"))
                    )
                    
                    # Сохраняем HTML страницы события
                    event_page_path = os.path.join(self.events_pages_dir, f"event_{keyword.replace(' ', '_')}_{i}.html")
                    with open(event_page_path, 'w', encoding='utf-8') as f:
                        f.write(self.driver.page_source)
                    logger.info(f"Сохранена страница события: {event_page_path}")
                    
                    # Закрываем вкладку и возвращаемся к результатам поиска
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                    
                except Exception as e:
                    logger.error(f"Ошибка при обработке карточки события {i}: {str(e)}")
                    # Если открыли новую вкладку, но произошла ошибка, закрываем её
                    if len(self.driver.window_handles) > 1:
                        self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[0])
            
            # Парсим сохраненные страницы событий
            parser = EventbriteParser()
            events = parser.parse_events()
            
            return events
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге страницы поиска: {str(e)}")
            return []

# Точка входа для запуска модуля напрямую
if __name__ == "__main__":
    # Список ключевых слов для поиска
    keywords = ["artificial intelligence", "machine learning", "data science", "startup", "tech conference"]
    
    # Создаем экземпляр класса и запускаем поиск
    eventbrite = EventbriteSelenium(headless=False)
    events = eventbrite.search_events(keywords)
    
    print(f"Найдено событий: {len(events)}")
    for event in events:
        print(f"- {event.title} ({event.start_date})")