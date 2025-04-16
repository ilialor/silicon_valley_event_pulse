import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.scraping.meetup import MeetupScraper
from app.services.scraping.eventbrite import EventbriteScraper
from app.services.scraping.techcrunch import TechCrunchScraper

class TestScrapers(unittest.TestCase):
    """Test cases for data scraping services"""
    
    @patch('app.services.scraping.meetup.requests.get')
    def test_meetup_scraper(self, mock_get):
        """Test MeetupScraper functionality"""
        # Mock the response from Meetup API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'events': [
                {
                    'id': '12345',
                    'name': 'Test Meetup Event',
                    'description': 'This is a test meetup event',
                    'local_date': '2025-04-20',
                    'local_time': '19:00',
                    'venue': {
                        'name': 'Test Venue',
                        'address_1': '123 Test St',
                        'city': 'San Francisco',
                        'state': 'CA'
                    },
                    'link': 'https://meetup.com/test-event',
                    'group': {
                        'name': 'Test Group'
                    }
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Initialize scraper and get events
        scraper = MeetupScraper()
        events = scraper.get_events('tech', 'San Francisco')
        
        # Assertions
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['title'], 'Test Meetup Event')
        self.assertEqual(events[0]['source'], 'Meetup')
        self.assertEqual(events[0]['location'], 'Test Venue, San Francisco, CA')
        self.assertEqual(events[0]['url'], 'https://meetup.com/test-event')
        
    @patch('app.services.scraping.eventbrite.requests.get')
    def test_eventbrite_scraper(self, mock_get):
        """Test EventbriteScraper functionality"""
        # Mock the response from Eventbrite API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'events': [
                {
                    'id': '67890',
                    'name': {
                        'text': 'Test Eventbrite Event'
                    },
                    'description': {
                        'text': 'This is a test eventbrite event'
                    },
                    'start': {
                        'local': '2025-04-25T10:00:00'
                    },
                    'end': {
                        'local': '2025-04-25T16:00:00'
                    },
                    'venue': {
                        'name': 'Eventbrite Venue',
                        'address': {
                            'address_1': '456 Event St',
                            'city': 'Palo Alto',
                            'region': 'CA'
                        }
                    },
                    'url': 'https://eventbrite.com/test-event',
                    'organizer': {
                        'name': 'Test Organizer'
                    }
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Initialize scraper and get events
        scraper = EventbriteScraper()
        events = scraper.get_events('tech', 'Palo Alto')
        
        # Assertions
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['title'], 'Test Eventbrite Event')
        self.assertEqual(events[0]['source'], 'Eventbrite')
        self.assertEqual(events[0]['location'], 'Eventbrite Venue, Palo Alto, CA')
        self.assertEqual(events[0]['url'], 'https://eventbrite.com/test-event')
        
    @patch('app.services.scraping.techcrunch.requests.get')
    def test_techcrunch_scraper(self, mock_get):
        """Test TechCrunchScraper functionality"""
        # Mock the response from TechCrunch website
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <body>
                <div class="event-card">
                    <h3 class="event-title">TechCrunch Disrupt 2025</h3>
                    <div class="event-description">Annual tech conference</div>
                    <div class="event-date">May 10, 2025</div>
                    <div class="event-location">San Francisco Convention Center</div>
                    <a href="https://techcrunch.com/events/disrupt-2025">Details</a>
                </div>
            </body>
        </html>
        """
        mock_get.return_value = mock_response
        
        # Initialize scraper and get events
        scraper = TechCrunchScraper()
        events = scraper.get_events()
        
        # Assertions
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['title'], 'TechCrunch Disrupt 2025')
        self.assertEqual(events[0]['source'], 'TechCrunch')
        self.assertEqual(events[0]['location'], 'San Francisco Convention Center')
        self.assertEqual(events[0]['url'], 'https://techcrunch.com/events/disrupt-2025')


if __name__ == '__main__':
    unittest.main()
