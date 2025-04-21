
from setuptools import setup, find_packages

setup(
    name="silicon_valley_events",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'aiohttp',
        'scrapy',
        'selenium',
        'sqlalchemy',
        'webdriver_manager',
        'beautifulsoup4',
    ],
)
