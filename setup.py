
from setuptools import setup, find_packages

setup(
    name="silicon_valley_events",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "scrapy>=2.6.0",
        "selenium>=4.1.0",
        "webdriver-manager>=3.8.0",
        "aiohttp>=3.8.1",
        "beautifulsoup4>=4.11.0",
        "sqlalchemy>=1.4.0",
        "alembic>=1.7.0",
        "asyncio>=3.4.3",
        "pandas>=1.4.0",
        "loguru>=0.6.0",
    ],
    author="Silicon Valley Events Team",
    author_email="example@example.com",
    description="Сборщик технологических событий в Силиконовой долине",
    keywords="events, silicon valley, tech, scraping",
    python_requires=">=3.8",
)
