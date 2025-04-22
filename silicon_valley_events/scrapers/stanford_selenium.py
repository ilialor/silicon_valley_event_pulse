import logging
import time
from typing import List, Optional
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime
from .selenium_base import BaseSeleniumScraper

logger = logging.getLogger(__name__)

class StanfordSeleniumScraper(BaseSeleniumScraper):
    """
    Скрейпер для сбора событий с сайта Stanford Events с использованием Selenium
    """
    
    def __init__(self, headless=True, timeout=10, max_pages=3):
        """
        Инициализация скрейпера
        
        Args:
            headless (bool): Запускать браузер в фоновом режиме
            timeout (int): Таймаут ожидания элементов в секундах
            max_pages (int): Максимальное количество страниц для сбора
        """
        super().__init__(headless, timeout)
        self.max_pages = max_pages
        self.source_name = "stanford"
    
    async def fetch_events(self, start_date=None, end_date=None):
        """
        Сбор событий с Stanford Events
        
        Args:
            start_date: Начальная дата для фильтрации событий
            end_date: Конечная дата для фильтрации событий
        
        Returns:
            List[Event]: Список собранных событий
        """
        try:
            self.setup_driver()
            
            # URL для поиска событий на Stanford
            url = "https://events.stanford.edu/"
            logger.info(f"Загрузка страницы Stanford Events: {url}")
            
            self.driver.get(url)
            time.sleep(3)  # Даем время для загрузки страницы
            
            # Собираем события с нескольких страниц
            current_page = 1
            
            while current_page <= self.max_pages:
                logger.info(f"Обработка страницы Stanford Events {current_page} из {self.max_pages}")
                
                # Ждем загрузки карточек событий
                event_cards = self.wait_for_elements(By.CSS_SELECTOR, "div.event-card, div.event-item")
                
                if not event_cards:
                    logger.warning("Не найдены карточки событий на странице Stanford Events")
                    break
                
                logger.info(f"Найдено {len(event_cards)} событий на странице Stanford Events")
                
                # Обрабатываем каждую карточку события
                for card in event_cards:
                    try:
                        # Извлекаем ссылку на событие
                        link_element = card.find_element(By.CSS_SELECTOR, "a.event-link, a.event-title")
                        event_url = link_element.get_attribute("href")
                        
                        # Открываем страницу события в новой вкладке
                        self.driver.execute_script("window.open(arguments[0]);", event_url)
                        
                        # Переключаемся на новую вкладку
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        
                        # Ждем загрузки страницы события
                        time.sleep(2)
                        
                        # Извлекаем информацию о событии
                        self._parse_event_page()
                        
                        # Закрываем вкладку и возвращаемся к списку событий
                        self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[0])
                        
                    except Exception as e:
                        logger.error(f"Ошибка при обработке карточки события Stanford: {str(e)}")
                
                # Переходим на следующую страницу, если она есть
                if current_page < self.max_pages:
                    try:
                        next_button = self.driver.find_element(By.CSS_SELECTOR, "a.next-page, a.pagination-next")
                        next_button.click()
                        time.sleep(3)  # Даем время для загрузки следующей страницы
                        current_page += 1
                    except NoSuchElementException:
                        logger.info("Достигнут конец списка событий Stanford")
                        break
                else:
                    break
            
            logger.info(f"Всего собрано событий Stanford: {self.event_count}")
            return self.events
            
        except Exception as e:
            logger.error(f"Ошибка при сборе событий Stanford: {str(e)}")
            return []
        finally:
            self.close()
    
    def _parse_event_page(self):
        """
        Парсинг страницы отдельного события
        """
        try:
            # Извлекаем заголовок события
            title_element = self.wait_for_element(By.CSS_SELECTOR, "h1.event-title, h1.title")
            title = self.clean_text(title_element.text) if title_element else "Без названия"
            
            # Извлекаем описание события
            description_element = self.wait_for_element(By.CSS_SELECTOR, "div.event-description, div.description")
            description = self.clean_text(description_element.text) if description_element else ""
            
            # Извлекаем дату события
            date_element = self.wait_for_element(By.CSS_SELECTOR, "time, span.date")
            date_str = date_element.text if date_element else ""
            start_date = self.extract_date(date_str) if date_str else datetime.now()
            
            # Извлекаем местоположение
            location_element = self.wait_for_element(By.CSS_SELECTOR, "div.location, span.location")
            location = self.clean_text(location_element.text) if location_element else ""
            
            # URL события
            url = self.driver.current_url
            
            # Извлекаем организатора
            organizer_element = self.wait_for_element(By.CSS_SELECTOR, "div.organizer, span.organizer")
            organizer = self.clean_text(organizer_element.text) if organizer_element else ""
            
            # Извлекаем теги
            tags = []
            tag_elements = self.driver.find_elements(By.CSS_SELECTOR, "a.event-category, span.category")
            for tag_element in tag_elements:
                tag = self.clean_text(tag_element.text)
                if tag:
                    tags.append(tag)
            
            # Извлекаем URL изображения
            image_element = self.wait_for_element(By.CSS_SELECTOR, "img.event-image, img.featured-image")
            image_url = image_element.get_attribute("src") if image_element else ""
            
            # Создаем объект события
            self.create_event(
                title=title,
                description=description,
                start_time=start_date,
                location=location,
                url=url,
                source=self.source_name,
                tags=tags,
                image_url=image_url,
                organizer=organizer,
                is_online=False  # По умолчанию считаем, что события Stanford не онлайн
            )
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге страницы события Stanford: {str(e)}")