import unittest
import sys
import os
from unittest.mock import patch, MagicMock
import json

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.llm.llm_manager import LLMManager

class TestGeminiIntegration(unittest.TestCase):
    """Test cases for Gemini API integration"""
    
    @patch('app.services.llm.llm_manager.requests.post')
    def test_gemini_api_connection(self, mock_post):
        """Test connection to Gemini API"""
        # Mock the response from Gemini API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'candidates': [
                {
                    'content': {
                        'parts': [
                            {
                                'text': 'Connection successful'
                            }
                        ]
                    }
                }
            ]
        }
        mock_post.return_value = mock_response
        
        # Initialize LLM manager and test connection
        llm_manager = LLMManager()
        result = llm_manager.test_connection("gemini", "test_api_key")
        
        # Assertions
        self.assertTrue(result['success'])
        self.assertIn('message', result)
    
    @patch('app.services.llm.llm_manager.requests.post')
    def test_gemini_api_error_handling(self, mock_post):
        """Test error handling for Gemini API"""
        # Mock an error response from Gemini API
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            'error': {
                'code': 401,
                'message': 'Invalid API key'
            }
        }
        mock_post.return_value = mock_response
        
        # Initialize LLM manager and test connection with invalid key
        llm_manager = LLMManager()
        result = llm_manager.test_connection("gemini", "invalid_api_key")
        
        # Assertions
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('Invalid API key', result['error'])
    
    @patch('app.services.llm.llm_manager.requests.post')
    def test_gemini_api_prompt_formatting(self, mock_post):
        """Test prompt formatting for Gemini API"""
        # Mock the response from Gemini API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'candidates': [
                {
                    'content': {
                        'parts': [
                            {
                                'text': 'Response text'
                            }
                        ]
                    }
                }
            ]
        }
        mock_post.return_value = mock_response
        
        # Initialize LLM manager
        llm_manager = LLMManager()
        llm_manager.add_config(
            provider="gemini",
            api_key="test_api_key",
            model_name="gemini-pro",
            is_default=True
        )
        
        # Call a method that uses the Gemini API
        event = {
            'title': 'Test Event',
            'description': 'Test description'
        }
        llm_manager.categorize_event(event)
        
        # Get the call arguments
        call_args = mock_post.call_args[1]
        request_json = json.loads(call_args['data'])
        
        # Assertions
        self.assertIn('contents', request_json)
        self.assertIn('generationConfig', request_json)
        
        # Check prompt formatting
        prompt_text = request_json['contents'][0]['parts'][0]['text']
        self.assertIn('Test Event', prompt_text)
        self.assertIn('Test description', prompt_text)
        self.assertIn('categorize', prompt_text.lower())
    
    @patch('app.services.llm.llm_manager.requests.post')
    def test_gemini_api_response_parsing(self, mock_post):
        """Test response parsing from Gemini API"""
        # Mock a JSON response from Gemini API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'candidates': [
                {
                    'content': {
                        'parts': [
                            {
                                'text': '{"key1": "value1", "key2": 42, "key3": ["item1", "item2"]}'
                            }
                        ]
                    }
                }
            ]
        }
        mock_post.return_value = mock_response
        
        # Initialize LLM manager
        llm_manager = LLMManager()
        llm_manager.add_config(
            provider="gemini",
            api_key="test_api_key",
            model_name="gemini-pro",
            is_default=True
        )
        
        # Call a method that parses JSON from the response
        event = {
            'title': 'Test Event',
            'description': 'Test description'
        }
        result = llm_manager.categorize_event(event)
        
        # Assertions
        self.assertIsInstance(result, dict)
        self.assertEqual(result['key1'], 'value1')
        self.assertEqual(result['key2'], 42)
        self.assertIsInstance(result['key3'], list)
        self.assertEqual(len(result['key3']), 2)


if __name__ == '__main__':
    unittest.main()
