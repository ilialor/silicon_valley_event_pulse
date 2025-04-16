import unittest
import sys
import os
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.models import Event, EventSource, EventCategory, LLMConfig, LLMAnalysis

class TestModels(unittest.TestCase):
    """Test cases for database models"""
    
    def test_event_model(self):
        """Test Event model creation and properties"""
        event = Event(
            title="Test Event",
            description="This is a test event",
            start_date=datetime.now(),
            end_date=datetime.now(),
            location="Test Location",
            url="https://example.com/event",
            event_type="in-person",
            source_id=1
        )
        
        self.assertEqual(event.title, "Test Event")
        self.assertEqual(event.description, "This is a test event")
        self.assertEqual(event.location, "Test Location")
        self.assertEqual(event.url, "https://example.com/event")
        self.assertEqual(event.event_type, "in-person")
        self.assertEqual(event.source_id, 1)
    
    def test_event_source_model(self):
        """Test EventSource model creation and properties"""
        source = EventSource(
            name="Test Source",
            url="https://example.com",
            description="Test source description",
            last_scraped=datetime.now()
        )
        
        self.assertEqual(source.name, "Test Source")
        self.assertEqual(source.url, "https://example.com")
        self.assertEqual(source.description, "Test source description")
    
    def test_event_category_model(self):
        """Test EventCategory model creation and properties"""
        category = EventCategory(
            name="Test Category",
            description="Test category description",
            event_id=1
        )
        
        self.assertEqual(category.name, "Test Category")
        self.assertEqual(category.description, "Test category description")
        self.assertEqual(category.event_id, 1)
    
    def test_llm_config_model(self):
        """Test LLMConfig model creation and properties"""
        config = LLMConfig(
            provider="gemini",
            api_key="test_api_key",
            model_name="gemini-pro",
            temperature=0.5,
            max_tokens=1024,
            is_default=True
        )
        
        self.assertEqual(config.provider, "gemini")
        self.assertEqual(config.api_key, "test_api_key")
        self.assertEqual(config.model_name, "gemini-pro")
        self.assertEqual(config.temperature, 0.5)
        self.assertEqual(config.max_tokens, 1024)
        self.assertTrue(config.is_default)
    
    def test_llm_analysis_model(self):
        """Test LLMAnalysis model creation and properties"""
        analysis = LLMAnalysis(
            event_id=1,
            analysis_type="categorization",
            result={"category": "AI/ML", "confidence": 0.95},
            llm_config_id=1,
            created_at=datetime.now()
        )
        
        self.assertEqual(analysis.event_id, 1)
        self.assertEqual(analysis.analysis_type, "categorization")
        self.assertEqual(analysis.result, {"category": "AI/ML", "confidence": 0.95})
        self.assertEqual(analysis.llm_config_id, 1)


if __name__ == '__main__':
    unittest.main()
