import logging
import time
import random
from typing import List, Optional
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from datetime import datetime
from .selenium_base import BaseSeleniumScraper
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import traceback

logger = logging.getLogger(__name__)

class MeetupSeleniumScraper(BaseSeleniumScraper):
    """
    Скрейпер для сбора событий с сайта Meetup с использованием Selenium
    """
    
    def __init__(self, headless=True, timeout=10, max_pages=3, proxy=None):
        """
        Инициализация скрейпера
        
        Args:
            headless (bool): Запускать браузер в фоновом режиме
            timeout (int): Таймаут ожидания элементов в секундах
            max_pages (int): Максимальное количество страниц для сбора
            proxy (str): Прокси-сервер в формате 'ip:port'
        """
        super().__init__(headless, timeout)
        self.max_pages = max_pages
        self.source_name = "meetup"
        self.proxy = proxy
    
    async def fetch_events(self, start_date=None, end_date=None):
        """
        Сбор событий с Meetup
        
        Args:
            start_date: Начальная дата для фильтрации событий
            end_date: Конечная дата для фильтрации событий
        
        Returns:
            List[Event]: Список собранных событий
        """
        try:
            logger.info("Инициализация драйвера Selenium для Meetup")
            try:
                self.setup_driver(proxy=self.proxy)
                logger.info("Драйвер Selenium успешно инициализирован")
            except WebDriverException as e:
                logger.error(f"Ошибка при инициализации драйвера Selenium: {str(e)}")
                logger.error(traceback.format_exc())
                return []
            
            # Устанавливаем параметры для маскировки Selenium
            try:
                self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    """
                })
                logger.info("Параметры маскировки Selenium установлены")
            except Exception as e:
                logger.warning(f"Не удалось установить параметры маскировки Selenium: {str(e)}")
            
            # URL для поиска событий в Кремниевой долине
            # Используем альтернативный URL, который может быть более стабильным
            url = "https://www.meetup.com/find/?location=us--ca--silicon-valley&source=EVENTS"
            logger.info(f"Загрузка страницы Meetup: {url}")
            
            # Устанавливаем заголовки для имитации обычного браузера
            try:
                self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                    "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                })
                logger.info("User-Agent успешно установлен")
            except Exception as e:
                logger.warning(f"Не удалось установить User-Agent: {str(e)}")
            
            # Увеличиваем таймаут загрузки страницы
            self.driver.set_page_load_timeout(60)
            
            # Загружаем страницу
            try:
                self.driver.get(url)
                logger.info("Страница успешно загружена")
            except Exception as e:
                logger.error(f"Ошибка при загрузке страницы: {str(e)}")
                # Пробуем альтернативный URL
                try:
                    alt_url = "https://www.meetup.com/find/?eventType=online&source=EVENTS"
                    logger.info(f"Пробуем альтернативный URL: {alt_url}")
                    self.driver.get(alt_url)
                    logger.info("Альтернативная страница успешно загружена")
                except Exception as e:
                    logger.error(f"Ошибка при загрузке альтернативной страницы: {str(e)}")
                    return []
            
            # Имитируем поведение человека
            self.simulate_human_behavior()
            
            # Увеличиваем время ожидания загрузки страницы
            time.sleep(15)  # Увеличиваем до 15 секунд
            
            # Проверяем, загрузилась ли страница
            try:
                # Ждем появления элементов на странице с увеличенным таймаутом
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.eventCard, div.event-card, article.event-card"))
                )
                logger.info("Страница Meetup успешно загружена")
            except TimeoutException:
                logger.warning("Не удалось дождаться загрузки элементов на странице Meetup")
                
                # Пробуем альтернативный URL
                alt_url = "https://www.meetup.com/find/?eventType=online&source=EVENTS"
                logger.info(f"Пробуем альтернативный URL: {alt_url}")
                self.driver.get(alt_url)
                time.sleep(15)
                
                # Проверяем загрузку альтернативного URL
                try:
                    WebDriverWait(self.driver, 30).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.eventCard, div.event-card, article.event-card"))
                    )
                    logger.info("Альтернативная страница Meetup успешно загружена")
                except TimeoutException:
                    logger.error("Не удалось загрузить страницу Meetup даже с альтернативным URL")
                    return []
            
            # Делаем скриншот для отладки
            try:
                self.driver.save_screenshot("meetup_loaded.png")
                logger.info("Сохранен скриншот загруженной страницы Meetup")
            except Exception as e:
                logger.warning(f"Не удалось сохранить скриншот: {str(e)}")
            
            # Собираем события с нескольких страниц
            current_page = 1
            
            while current_page <= self.max_pages:
                logger.info(f"Обработка страницы Meetup {current_page} из {self.max_pages}")
                
                # Прокручиваем страницу вниз для загрузки всех событий
                for _ in range(5):  # Увеличиваем количество прокруток
                    self.scroll_down(300)
                    time.sleep(2)  # Увеличиваем задержку между прокрутками
                
                # Имитируем поведение человека
                self.simulate_human_behavior()
                
                # Ждем загрузки карточек событий с увеличенным таймаутом
                try:
                    event_cards = WebDriverWait(self.driver, 20).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.eventCard, div.event-card, article.event-card"))
                    )
                except TimeoutException:
                    logger.warning("Не удалось найти карточки событий на странице Meetup")
                    # Пробуем другие селекторы
                    try:
                        event_cards = self.driver.find_elements(By.CSS_SELECTOR, "div[data-event-id], div.event-listing")
                    except:
                        event_cards = []
                
                if not event_cards:
                    logger.warning("Не найдены карточки событий на странице Meetup")
                    break
                
                logger.info(f"Найдено {len(event_cards)} событий на странице Meetup")
                
                # Обрабатываем каждую карточку события
                for card in event_cards[:3]:  # Ограничиваем количество событий для тестирования
                    try:
                        # Извлекаем ссылку на событие
                        try:
                            link_element = card.find_element(By.CSS_SELECTOR, "a.eventCard--link, a.event-card-link, a[href*='/events/']")
                            event_url = link_element.get_attribute("href")
                        except NoSuchElementException:
                            # Если не удалось найти ссылку, пробуем другие селекторы
                            try:
                                link_element = card.find_element(By.TAG_NAME, "a")
                                event_url = link_element.get_attribute("href")
                            except:
                                logger.warning("Не удалось найти ссылку на событие")
                                continue
                        
                        if not event_url or not event_url.startswith("http"):
                            logger.warning(f"Некорректная ссылка на событие: {event_url}")
                            continue
                        
                        logger.info(f"Обработка события по ссылке: {event_url}")
                        
                        # Открываем страницу события в новой вкладке
                        self.driver.execute_script("window.open(arguments[0]);", event_url)
                        
                        # Переключаемся на новую вкладку
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        
                        # Ждем загрузки страницы события
                        time.sleep(5)
                        
                        # Имитируем поведение человека
                        self.simulate_human_behavior()
                        
                        # Делаем скриншот для отладки
                        self.driver.save_screenshot(f"meetup_event_{current_page}_{event_cards.index(card)}.png")
                        
                        # Извлекаем информацию о событии
                        self._parse_event_page()
                        
                        # Закрываем вкладку и возвращаемся к списку событий
                        self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[0])
                        
                        # Небольшая пауза между обработкой событий
                        time.sleep(2)
                        
                    except Exception as e:
                        logger.error(f"Ошибка при обработке карточки события Meetup: {str(e)}")
                        # Если произошла ошибка, убедимся, что мы вернулись к основной вкладке
                        if len(self.driver.window_handles) > 1:
                            self.driver.close()
                            self.driver.switch_to.window(self.driver.window_handles[0])
                
                # Переходим на следующую страницу, если она есть
                if current_page < self.max_pages:
                    try:
                        next_button = self.driver.find_element(By.CSS_SELECTOR, "button.pagination-next, a.pagination-next, button[aria-label='Next']")
                        next_button.click()
                        time.sleep(5)  # Увеличиваем время ожидания загрузки следующей страницы
                        current_page += 1
                    except NoSuchElementException:
                        logger.info("Достигнут конец списка событий Meetup")
                        break
                else:
                    break
            
            logger.info(f"Всего собрано событий Meetup: {self.event_count}")
            return self.events
            
        except Exception as e:
            logger.error(f"Ошибка при сборе событий Meetup: {str(e)}")
            logger.error(traceback.format_exc())
            return []
        finally:
            try:
                self.close()
                logger.info("Драйвер Selenium успешно закрыт")
            except Exception as e:
                logger.warning(f"Ошибка при закрытии драйвера: {str(e)}")
    
    def _parse_event_page(self):
        """
        Парсинг страницы отдельного события
        """
        try:
            # Ждем загрузки страницы события
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
            
            # Извлекаем заголовок события
            try:
                title_element = self.driver.find_element(By.CSS_SELECTOR, "h1.event-title, h1.pageTitle, h1")
                title = self.clean_text(title_element.text) if title_element else "Без названия"
            except NoSuchElementException:
                title = "Без названия"
            
            # Извлекаем описание события
            try:
                description_element = self.driver.find_element(By.CSS_SELECTOR, "div.event-description, div.eventDescription, div[data-testid='event-description']")
                description = self.clean_text(description_element.text) if description_element else ""
            except NoSuchElementException:
                description = ""
            
            # Извлекаем дату события
            try:
                date_element = self.driver.find_element(By.CSS_SELECTOR, "time, span.eventTimeDisplay, div[data-testid='event-when-display']")
                date_str = date_element.text if date_element else ""
                start_date = self.extract_date(date_str) if date_str else datetime.now()
            except NoSuchElementException:
                start_date = datetime.now()
            
            # Извлекаем местоположение
            try:
                location_element = self.driver.find_element(By.CSS_SELECTOR, "address.venueDisplay, div.event-location, div[data-testid='event-where-display']")
                location = self.clean_text(location_element.text) if location_element else ""
            except NoSuchElementException:
                location = ""
            
            # URL события
            url = self.driver.current_url
            
            # Извлекаем организатора
            try:
                organizer_element = self.driver.find_element(By.CSS_SELECTOR, "div.groupNameLink, div.event-host, a[data-testid='group-name']")
                organizer = self.clean_text(organizer_element.text) if organizer_element else ""
            except NoSuchElementException:
                organizer = ""
            
            # Извлекаем теги
            try:
                tags_elements = self.driver.find_elements(By.CSS_SELECTOR, "span.eventTag, a.event-category, span[data-testid='tag-item']")
                tags = [self.clean_text(tag.text) for tag in tags_elements if tag.text]
            except:
                tags = []
            
            # Добавляем стандартный тег для всех событий Meetup
            if 'meetup' not in [t.lower() for t in tags]:
                tags.append('meetup')
            
            # Извлекаем URL изображения
            try:
                image_element = self.driver.find_element(By.CSS_SELECTOR, "img.eventImage, img.event-image, img[alt*='event'], img[data-testid='event-photo']")
                image_url = image_element.get_attribute("src")
            except NoSuchElementException:
                image_url = None
            
            # Определяем, является ли событие онлайн
            is_online = False
            if location:
                is_online = any(keyword in location.lower() for keyword in ['online', 'zoom', 'virtual', 'webinar'])
            else:
                # Проверяем по заголовку или описанию
                is_online = any(keyword in (title + description).lower() for keyword in ['online', 'zoom', 'virtual', 'webinar'])
            
            # Создаем объект события
            event = self.create_event(
                title=title,
                description=description,
                start_time=start_date,
                end_time=None,
                location=location,
                url=url,
                tags=tags,
                image_url=image_url,
                organizer=organizer,
                is_online=is_online
            )
            
            logger.info(f"Собрано событие Meetup: {title}")
            return event
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге события Meetup: {str(e)}")
            return None
    
    def scroll_down(self, pixels=300):
        """
        Прокрутка страницы вниз
        
        Args:
            pixels (int): Количество пикселей для прокрутки
        """
        self.driver.execute_script(f"window.scrollBy(0, {pixels});")
    
    def simulate_human_behavior(self):
        """
        Имитация поведения человека на странице
        """
        try:
            # Случайная задержка
            delay = random.uniform(1, 3)
            logger.debug(f"Имитация задержки: {delay:.2f} сек")
            time.sleep(delay)
            
            # Случайные движения мышью
            actions = ActionChains(self.driver)
            for _ in range(3):
                x = random.randint(100, 700)
                y = random.randint(100, 500)
                actions.move_by_offset(x, y).perform()
                time.sleep(random.uniform(0.5, 1.5))
            
            # Случайная прокрутка
            scroll_amount = random.randint(100, 300)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(0.5, 1.5))
            
            # Иногда делаем клик на случайном месте страницы
            if random.random() > 0.7:
                x = random.randint(100, 700)
                y = random.randint(100, 500)
                actions.move_to_element_with_offset(self.driver.find_element(By.TAG_NAME, "body"), x, y).click().perform()
                time.sleep(random.uniform(0.5, 1))
                
            logger.debug("Имитация человеческого поведения выполнена")
        except Exception as e:
            logger.warning(f"Ошибка при имитации человеческого поведения: {str(e)}")

    def setup_driver(self, proxy=None):
        """
        Переопределение метода настройки драйвера с поддержкой прокси
        """
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        
        try:
            options = Options()
            if self.headless:
                options.add_argument("--headless")
            
            # Добавляем опции для обхода обнаружения автоматизации
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            
            # Добавляем случайный User-Agent
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15'
            ]
            options.add_argument(f"--user-agent={random.choice(user_agents)}")
            
            # Добавляем прокси, если он указан
            if proxy:
                options.add_argument(f'--proxy-server={proxy}')
                logger.info(f"Используется прокси: {proxy}")
            
            # Устанавливаем и настраиваем драйвер
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.set_page_load_timeout(self.timeout)
            
            logger.info("Драйвер Chrome успешно настроен")
            return True
        except Exception as e:
            logger.error(f"Ошибка при настройке драйвера Chrome: {str(e)}")
            logger.error(traceback.format_exc())
            raise