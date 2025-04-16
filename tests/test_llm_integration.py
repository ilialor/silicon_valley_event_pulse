import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.llm.llm_manager import LLMManager

class TestLLMIntegration(unittest.TestCase):
    """Test cases for LLM integration"""
    
    @patch('app.services.llm.llm_manager.requests.post')
    def test_gemini_categorization(self, mock_post):
        """Test event categorization with Gemini API"""
        # Mock the response from Gemini API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'candidates': [
                {
                    'content': {
                        'parts': [
                            {
                                'text': '{"category": "AI/ML", "subcategories": ["Artificial Intelligence", "Machine Learning", "Conference"], "confidence": 0.95}'
                            }
                        ]
                    }
                }
            ]
        }
        mock_post.return_value = mock_response
        
        # Initialize LLM manager and test categorization
        llm_manager = LLMManager()
        llm_manager.add_config(
            provider="gemini",
            api_key="test_api_key",
            model_name="gemini-pro",
            is_default=True
        )
        
        event = {
            'title': 'Silicon Valley AI Summit 2025',
            'description': 'Join industry leaders for a day of insights into the latest AI advancements and their impact on business and society.'
        }
        
        result = llm_manager.categorize_event(event)
        
        # Assertions
        self.assertIn('category', result)
        self.assertEqual(result['category'], 'AI/ML')
        self.assertIn('subcategories', result)
        self.assertIn('confidence', result)
        self.assertGreaterEqual(result['confidence'], 0.9)
    
    @patch('app.services.llm.llm_manager.requests.post')
    def test_gemini_summarization(self, mock_post):
        """Test event description summarization with Gemini API"""
        # Mock the response from Gemini API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'candidates': [
                {
                    'content': {
                        'parts': [
                            {
                                'text': 'A premier conference bringing together AI experts to discuss latest advancements and their business applications.'
                            }
                        ]
                    }
                }
            ]
        }
        mock_post.return_value = mock_response
        
        # Initialize LLM manager and test summarization
        llm_manager = LLMManager()
        llm_manager.add_config(
            provider="gemini",
            api_key="test_api_key",
            model_name="gemini-pro",
            is_default=True
        )
        
        event_description = """
        The Silicon Valley AI Summit 2025 is the premier gathering for AI professionals, researchers, and enthusiasts.
        This full-day conference will feature keynote presentations, panel discussions, and interactive workshops
        covering the latest advancements in artificial intelligence and machine learning.
        
        Topics will include generative AI applications, ethical considerations, AI for sustainability,
        human-AI collaboration, and advances in natural language processing and computer vision.
        """
        
        summary = llm_manager.summarize_event_description(event_description)
        
        # Assertions
        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 10)
        self.assertLess(len(summary), len(event_description))
    
    @patch('app.services.llm.llm_manager.requests.post')
    def test_gemini_trend_analysis(self, mock_post):
        """Test trend analysis with Gemini API"""
        # Mock the response from Gemini API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'candidates': [
                {
                    'content': {
                        'parts': [
                            {
                                'text': '[{"trend": "Generative AI Applications", "score": 92, "description": "The rise of practical applications for generative AI across industries is creating new opportunities for startups and enterprises."}, {"trend": "Web3 Development", "score": 85, "description": "Decentralized applications and blockchain technologies continue to evolve with a focus on scalability and user experience."}]'
                            }
                        ]
                    }
                }
            ]
        }
        mock_post.return_value = mock_response
        
        # Initialize LLM manager and test trend analysis
        llm_manager = LLMManager()
        llm_manager.add_config(
            provider="gemini",
            api_key="test_api_key",
            model_name="gemini-pro",
            is_default=True
        )
        
        events = [
            {
                'title': 'Silicon Valley AI Summit 2025',
                'category': 'AI/ML',
                'date': '2025-04-20'
            },
            {
                'title': 'Generative AI Workshop',
                'category': 'AI/ML',
                'date': '2025-05-05'
            },
            {
                'title': 'Blockchain Innovation Forum',
                'category': 'Blockchain',
                'date': '2025-04-25'
            },
            {
                'title': 'Web3 Developer Conference',
                'category': 'Blockchain',
                'date': '2025-06-05'
            }
        ]
        
        trends = llm_manager.analyze_trends(events)
        
        # Assertions
        self.assertIsInstance(trends, list)
        self.assertGreaterEqual(len(trends), 1)
        self.assertIn('trend', trends[0])
        self.assertIn('score', trends[0])
        self.assertIn('description', trends[0])


if __name__ == '__main__':
    unittest.main()
