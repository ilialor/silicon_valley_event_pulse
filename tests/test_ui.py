import unittest
import sys
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestUserInterface(unittest.TestCase):
    """Test cases for user interface"""
    
    @classmethod
    def setUpClass(cls):
        """Set up the WebDriver for UI testing"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.base_url = "http://localhost:8000"
    
    @classmethod
    def tearDownClass(cls):
        """Close the WebDriver after testing"""
        cls.driver.quit()
    
    def test_home_page_loads(self):
        """Test that the home page loads correctly"""
        self.driver.get(f"{self.base_url}/index.html")
        
        # Check title
        self.assertIn("Silicon Valley Event Pulse", self.driver.title)
        
        # Check main components
        self.assertTrue(self.driver.find_element(By.CLASS_NAME, "hero-section").is_displayed())
        self.assertTrue(self.driver.find_element(By.CLASS_NAME, "search-box").is_displayed())
        self.assertTrue(self.driver.find_element(By.CLASS_NAME, "navbar").is_displayed())
        
        # Check navigation links
        nav_links = self.driver.find_elements(By.CLASS_NAME, "nav-link")
        self.assertGreaterEqual(len(nav_links), 4)  # Home, Calendar, Trends, LLM Settings
    
    def test_calendar_page_loads(self):
        """Test that the calendar page loads correctly"""
        self.driver.get(f"{self.base_url}/calendar.html")
        
        # Check title
        self.assertIn("Calendar", self.driver.title)
        
        # Check calendar components
        self.assertTrue(self.driver.find_element(By.CLASS_NAME, "calendar-container").is_displayed())
        self.assertTrue(self.driver.find_element(By.CLASS_NAME, "calendar-days").is_displayed())
        
        # Check calendar days
        calendar_days = self.driver.find_elements(By.CLASS_NAME, "calendar-day")
        self.assertGreaterEqual(len(calendar_days), 28)  # At least 28 days in a month
    
    def test_event_details_page_loads(self):
        """Test that the event details page loads correctly"""
        self.driver.get(f"{self.base_url}/event_details.html")
        
        # Check title
        self.assertIn("Event Details", self.driver.title)
        
        # Check event details components
        self.assertTrue(self.driver.find_element(By.CLASS_NAME, "event-container").is_displayed())
        self.assertTrue(self.driver.find_element(By.CLASS_NAME, "event-title").is_displayed())
        self.assertTrue(self.driver.find_element(By.CLASS_NAME, "event-meta").is_displayed())
        
        # Check event title
        event_title = self.driver.find_element(By.CLASS_NAME, "event-title").text
        self.assertEqual(event_title, "Silicon Valley AI Summit 2025")
    
    def test_trends_page_loads(self):
        """Test that the trends page loads correctly"""
        self.driver.get(f"{self.base_url}/trends.html")
        
        # Check title
        self.assertIn("Trends", self.driver.title)
        
        # Check trends components
        self.assertTrue(self.driver.find_element(By.CLASS_NAME, "content-container").is_displayed())
        
        # Check trend cards
        trend_cards = self.driver.find_elements(By.CLASS_NAME, "trend-card")
        self.assertGreaterEqual(len(trend_cards), 3)  # At least 3 trend cards
    
    def test_llm_settings_page_loads(self):
        """Test that the LLM settings page loads correctly"""
        self.driver.get(f"{self.base_url}/llm_settings.html")
        
        # Check title
        self.assertIn("LLM Settings", self.driver.title)
        
        # Check settings components
        self.assertTrue(self.driver.find_element(By.CLASS_NAME, "settings-section").is_displayed())
        
        # Check API key cards
        api_key_cards = self.driver.find_elements(By.CLASS_NAME, "api-key-card")
        self.assertGreaterEqual(len(api_key_cards), 1)  # At least 1 API key card
    
    def test_search_functionality(self):
        """Test the search functionality on the home page"""
        self.driver.get(f"{self.base_url}/index.html")
        
        # Find search input and submit button
        search_input = self.driver.find_element(By.CSS_SELECTOR, ".search-box input[type='text']")
        search_button = self.driver.find_element(By.CSS_SELECTOR, ".search-box button[type='submit']")
        
        # Enter search query
        search_input.clear()
        search_input.send_keys("AI")
        
        # Submit search
        search_button.click()
        
        # Wait for results (in a real application, this would navigate to results page)
        # For this test, we just verify the form submission worked without errors
        self.assertIn("Silicon Valley Event Pulse", self.driver.title)
    
    def test_responsive_design(self):
        """Test responsive design at different screen sizes"""
        self.driver.get(f"{self.base_url}/index.html")
        
        # Test desktop size
        self.driver.set_window_size(1200, 800)
        self.assertTrue(self.driver.find_element(By.CLASS_NAME, "navbar-nav").is_displayed())
        
        # Test tablet size
        self.driver.set_window_size(768, 1024)
        
        # Test mobile size
        self.driver.set_window_size(375, 667)
        # On mobile, the navbar is collapsed
        navbar_toggler = self.driver.find_element(By.CLASS_NAME, "navbar-toggler")
        self.assertTrue(navbar_toggler.is_displayed())


if __name__ == '__main__':
    unittest.main()
