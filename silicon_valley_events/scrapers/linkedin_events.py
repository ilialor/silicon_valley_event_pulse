import logging
from datetime import datetime
from typing import List, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ..models.event import Event
from .base import SeleniumEventScraper

logger = logging.getLogger(__name__)

class LinkedInEventsScraper(SeleniumEventScraper):
    """
    Скрейпер для сбора событий с LinkedIn
    """
    
    def __init__(self, email: str, password: str, headless: bool = True):
        """
        Инициализирует скрейпер LinkedIn
        
        Args:
            email: Email для входа в LinkedIn
            password: Пароль для входа в LinkedIn
            headless: Запускать браузер в фоновом режиме без GUI
        """
        super().__init__(headless)
        self.email = email
        self.password = password
        self.logged_in = False
    
    async def login(self):
        """
        Выполняет вход в LinkedIn
        """
        if self.logged_in:
            return True
            
        try:
            if not self.driver:
                self.setup_driver()
                
            self.driver.get("https://www.linkedin.com/login")
            
            # Ввод email
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_input.send_keys(self.email)
            
            # Ввод пароля
            password_input = self.driver.find_element(By.ID, "password")
            password_input.send_keys(self.password)
            
            # Нажатие кнопки входа
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            # Ожидание загрузки страницы
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".feed-identity-module"))
            )
            
            self.logged_in = True
            logger.info("Успешный вход в LinkedIn")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при входе в LinkedIn: {str(e)}")
            return False
    
    async def fetch_events(self, start_date: datetime, end_date: datetime) -> List[Event]:
        """
        Извлекает события LinkedIn в указанном диапазоне дат
        
        Args:
            start_date: Начальная дата
            end_date: Конечная дата
            
        Returns:
            List[Event]: Список событий
        """
        events = []
        
        try:
            if not self.logged_in:
                success = await self.login()
                if not success:
                    logger.error("Не удалось войти в LinkedIn")
                    return events
            
            # Переход на страницу событий
            self.driver.get("https://www.linkedin.com/events/")
            
            # Прокрутка страницы для загрузки всех событий
            self.scroll_to_bottom(scroll_pause_time=2.0, max_scrolls=5)
            
            # Получение всех карточек событий
            event_cards = self.driver.find_elements(By.CSS_SELECTOR, ".event-card")
            
            logger.info(f"Найдено {len(event_cards)} событий на LinkedIn")
            
            for card in event_cards:
                try:
                    # Извлечение данных о событии
                    title_element = card.find_element(By.CSS_SELECTOR, ".event-card__title")
                    title = title_element.text
                    
                    # Получение URL события
                    url = title_element.get_attribute("href")
                    
                    # Получение даты события
                    date_element = card.find_element(By.CSS_SELECTOR, ".event-card__date")
                    date_str = date_element.text
                    event_date = self.extract_date(date_str)
                    
                    # Проверка, входит ли дата в указанный диапазон
                    if event_date and start_date <= event_date <= end_date:
                        # Получение дополнительной информации о событии
                        location_element = card.find_element(By.CSS_SELECTOR, ".event-card__location")
                        location = location_element.text
                        
                        # Создание объекта события
                        event = self.create_event(
                            title=title,
                            start_date=event_date,
                            location=location,
                            url=url,
                            source="linkedin"
                        )
                        
                        events.append(event)
                        
                except Exception as e:
                    logger.error(f"Ошибка при обработке карточки события LinkedIn: {str(e)}")
                    continue
            
            return events
            
        except Exception as e:
            logger.error(f"Ошибка при сборе событий LinkedIn: {str(e)}")
            return events