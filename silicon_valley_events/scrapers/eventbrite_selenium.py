import logging
import time
from typing import List, Optional
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime
import json
from .selenium_base import BaseSeleniumScraper

logger = logging.getLogger(__name__)

class EventbriteSeleniumScraper(BaseSeleniumScraper):
    """
    Скрейпер для сбора событий с сайта Eventbrite с использованием Selenium
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
        self.source_name = "eventbrite"
    
    async def fetch_events(self, start_date=None, end_date=None):
        """
        Сбор событий с Eventbrite
        
        Args:
            start_date: Начальная дата для фильтрации событий
            end_date: Конечная дата для фильтрации событий
        
        Returns:
            List[Event]: Список собранных событий
        """
        try:
            self.setup_driver()
            
            # URL для поиска событий в Сан-Франциско
            url = "https://www.eventbrite.com/d/ca--san-francisco/events/"
            logger.info(f"Загрузка страницы Eventbrite: {url}")
            
            self.driver.get(url)
            time.sleep(3)  # Даем время для загрузки страницы
            
            # Собираем события с нескольких страниц
            current_page = 1
            
            while current_page <= self.max_pages:
                logger.info(f"Обработка страницы Eventbrite {current_page} из {self.max_pages}")
                
                # Ждем загрузки карточек событий
                event_cards = self.wait_for_elements(By.CSS_SELECTOR, "div.search-event-card-wrapper, article.event-card")
                
                if not event_cards:
                    logger.warning("Не найдены карточки событий на странице Eventbrite")
                    break
                
                logger.info(f"Найдено {len(event_cards)} событий на странице Eventbrite")
                
                # Обрабатываем каждую карточку события
                for card in event_cards:
                    try:
                        # Извлекаем ссылку на событие
                        link_element = card.find_element(By.CSS_SELECTOR, "a.event-card-link, a.eds-event-card-content__action-link")
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
                        logger.error(f"Ошибка при обработке карточки события Eventbrite: {str(e)}")
                
                # Переходим на следующую страницу, если она есть
                if current_page < self.max_pages:
                    try:
                        next_button = self.driver.find_element(By.CSS_SELECTOR, "a[data-spec='page-next']")
                        next_button.click()
                        time.sleep(3)  # Даем время для загрузки следующей страницы
                        current_page += 1
                    except NoSuchElementException:
                        logger.info("Достигнут конец списка событий Eventbrite")
                        break
                else:
                    break
            
            logger.info(f"Всего собрано событий Eventbrite: {self.event_count}")
            return self.events
            
        except Exception as e:
            logger.error(f"Ошибка при сборе событий Eventbrite: {str(e)}")
            return []
        finally:
            self.close()
    
    def _parse_event_page(self):
        """
        Парсинг страницы отдельного события
        """
        try:
            # Извлекаем заголовок события
            title_element = self.wait_for_element(By.CSS_SELECTOR, "h1.event-title, h1.eds-text-hl")
            title = self.clean_text(title_element.text) if title_element else "Без названия"
            
            # Извлекаем описание события
            description_element = self.wait_for_element(By.CSS_SELECTOR, "div.event-description, div.eds-text-bs")
            description = self.clean_text(description_element.text) if description_element else ""
            
            # Извлекаем дату события
            date_element = self.wait_for_element(By.CSS_SELECTOR, "time, p.date-info")
            date_str = date_element.text if date_element else ""
            start_date = self.extract_date(date_str) if date_str else datetime.now()
            
            # Извлекаем местоположение
            location_element = self.wait_for_element(By.CSS_SELECTOR, "div.event-details__data, p.location-info")
            location = self.clean_text(location_element.text) if location_element else ""
            
            # URL события
            url = self.driver.current_url
            
            # Извлекаем организатора
            organizer_element = self.wait_for_element(By.CSS_SELECTOR, "a.js-d-scroll-to, a.organizer-name")
            organizer = self.clean_text(organizer_element.text) if organizer_element else ""
            
            # Извлекаем теги
            tags = []
            tag_elements = self.driver.find_elements(By.CSS_SELECTOR, "a.js-event-categories, a.event-category")
            for tag_element in tag_elements:
                tag = self.clean_text(tag_element.text)
                if tag:
                    tags.append(tag)
            
            # Извлекаем URL изображения
            image_element = self.wait_for_element(By.CSS_SELECTOR, "picture img, img.event-logo")
            image_url = image_element.get_attribute("src") if image_element else ""
            
            # Определяем, является ли событие онлайн
            is_online = False
            if location:
                is_online = any(keyword in location.lower() for keyword in ['online', 'zoom', 'virtual', 'webinar'])
            else:
                # Проверяем по заголовку или описанию
                is_online = any(keyword in (title + description).lower() for keyword in ['online', 'zoom', 'virtual', 'webinar'])
            
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
                is_online=is_online
            )
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге страницы события Eventbrite: {str(e)}")