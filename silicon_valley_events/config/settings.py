
import os
from pathlib import Path

# Базовые пути
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"

# API ключи
MEETUP_API_KEY = os.environ.get("MEETUP_API_KEY", "YOUR_MEETUP_API_KEY")
EVENTBRITE_API_KEY = os.environ.get("EVENTBRITE_API_KEY", "YOUR_EVENTBRITE_API_KEY")
LINKEDIN_EMAIL = os.environ.get("LINKEDIN_EMAIL", "YOUR_LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.environ.get("LINKEDIN_PASSWORD", "YOUR_LINKEDIN_PASSWORD")

# Database configuration
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///events.db")

# Scraping configuration
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
]

# Rate limiting (requests per minute)
RATE_LIMITS = {
    "meetup": 30,
    "eventbrite": 30,
    "linkedin": 15,
    "stanford": 20,
    "default": 10
}

# Настройки Scrapy
SCRAPY_SETTINGS = {
    'BOT_NAME': 'silicon_valley_events',
    'ROBOTSTXT_OBEY': True,
    'DOWNLOAD_DELAY': 3,
    'CONCURRENT_REQUESTS': 16,
    'COOKIES_ENABLED': False,
    'TELNETCONSOLE_ENABLED': False,
    'DEFAULT_REQUEST_HEADERS': {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en',
    },
}

# Настройки Selenium
SELENIUM_SETTINGS = {
    'HEADLESS': True,
    'WINDOW_SIZE': '1920x1080',
    'IMPLICIT_WAIT': 10,
    'PAGE_LOAD_TIMEOUT': 30,
}

# Настройки логирования
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': str(LOG_DIR / 'app.log'),
            'formatter': 'standard',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Создание необходимых директорий
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
