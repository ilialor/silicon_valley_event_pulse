import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

class TestAPIEndpoints(unittest.TestCase):
    """Test cases for API endpoints"""
    
    def setUp(self):
        """Set up test client"""
        self.client = TestClient(app)
    
    def test_get_events(self):
        """Test GET /events endpoint"""
        response = self.client.get("/api/events")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
    
    def test_get_event_by_id(self):
        """Test GET /events/{event_id} endpoint"""
        # Mock event ID
        event_id = 1
        
        response = self.client.get(f"/api/events/{event_id}")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("id", response.json())
        self.assertEqual(response.json()["id"], event_id)
    
    def test_search_events(self):
        """Test GET /events/search endpoint"""
        response = self.client.get("/api/events/search?query=AI&category=AI/ML&start_date=2025-04-01")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
    
    def test_get_categories(self):
        """Test GET /categories endpoint"""
        response = self.client.get("/api/categories")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
    
    def test_get_trends(self):
        """Test GET /trends endpoint"""
        response = self.client.get("/api/trends")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
        for trend in response.json():
            self.assertIn("trend", trend)
            self.assertIn("score", trend)
            self.assertIn("description", trend)
    
    def test_get_llm_configs(self):
        """Test GET /llm/configs endpoint"""
        response = self.client.get("/api/llm/configs")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
    
    def test_add_llm_config(self):
        """Test POST /llm/configs endpoint"""
        config_data = {
            "provider": "gemini",
            "api_key": "test_api_key",
            "model_name": "gemini-pro",
            "temperature": 0.5,
            "max_tokens": 1024,
            "is_default": True
        }
        
        response = self.client.post("/api/llm/configs", json=config_data)
        self.assertEqual(response.status_code, 201)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("id", response.json())
        self.assertEqual(response.json()["provider"], config_data["provider"])
    
    def test_test_llm_connection(self):
        """Test POST /llm/test endpoint"""
        test_data = {
            "provider": "gemini",
            "api_key": "test_api_key"
        }
        
        response = self.client.post("/api/llm/test", json=test_data)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("status", response.json())
        self.assertIn("message", response.json())
    
    def test_analyze_event(self):
        """Test POST /events/{event_id}/analyze endpoint"""
        # Mock event ID
        event_id = 1
        
        response = self.client.post(f"/api/events/{event_id}/analyze", json={"analysis_type": "categorization"})
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("event_id", response.json())
        self.assertIn("analysis_type", response.json())
        self.assertIn("result", response.json())


if __name__ == '__main__':
    unittest.main()
