from typing import Dict, List, Optional, Any
import google.generativeai as genai
import logging
import json
from cryptography.fernet import Fernet
import os
import base64

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.models import LLMSetting

logger = logging.getLogger(__name__)

class LLMManager:
    """
    Менеджер для работы с языковыми моделями (ЛЛМ)
    """
    
    def __init__(self):
        self.db = SessionLocal()
        self._encryption_key = self._get_or_create_encryption_key()
        self._fernet = Fernet(self._encryption_key)
        
    def __del__(self):
        self.db.close()
    
    def _get_or_create_encryption_key(self) -> bytes:
        """
        Получение или создание ключа шифрования для API ключей
        
        Returns:
            Ключ шифрования
        """
        key_file = ".encryption_key"
        
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(key)
            return key
    
    def _encrypt_api_key(self, api_key: str) -> str:
        """
        Шифрование API ключа
        
        Args:
            api_key: API ключ
            
        Returns:
            Зашифрованный API ключ
        """
        return self._fernet.encrypt(api_key.encode()).decode()
    
    def _decrypt_api_key(self, encrypted_api_key: str) -> str:
        """
        Расшифровка API ключа
        
        Args:
            encrypted_api_key: Зашифрованный API ключ
            
        Returns:
            Расшифрованный API ключ
        """
        return self._fernet.decrypt(encrypted_api_key.encode()).decode()
    
    def add_llm_setting(self, provider: str, model_name: str, api_key: str, 
                       endpoint_url: Optional[str] = None, is_active: bool = False, 
                       priority: int = 0) -> Dict:
        """
        Добавление настроек ЛЛМ
        
        Args:
            provider: Провайдер ЛЛМ (google, openai, anthropic, self-hosted)
            model_name: Название модели
            api_key: API ключ
            endpoint_url: URL эндпоинта (для self-hosted моделей)
            is_active: Активна ли модель
            priority: Приоритет использования
            
        Returns:
            Словарь с информацией о добавленных настройках
        """
        try:
            # Шифруем API ключ
            encrypted_api_key = self._encrypt_api_key(api_key)
            
            # Создаем новую запись в базе данных
            llm_setting = LLMSetting(
                provider=provider,
                model_name=model_name,
                api_key=encrypted_api_key,
                endpoint_url=endpoint_url,
                is_active=is_active,
                priority=priority
            )
            
            self.db.add(llm_setting)
            self.db.commit()
            self.db.refresh(llm_setting)
            
            return {
                "setting_id": llm_setting.setting_id,
                "provider": llm_setting.provider,
                "model_name": llm_setting.model_name,
                "is_active": llm_setting.is_active,
                "priority": llm_setting.priority
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding LLM setting: {str(e)}")
            raise
    
    def update_llm_setting(self, setting_id: int, **kwargs) -> Dict:
        """
        Обновление настроек ЛЛМ
        
        Args:
            setting_id: ID настроек
            **kwargs: Параметры для обновления
            
        Returns:
            Словарь с информацией об обновленных настройках
        """
        try:
            # Получаем настройки
            llm_setting = self.db.query(LLMSetting).filter(
                LLMSetting.setting_id == setting_id
            ).first()
            
            if not llm_setting:
                raise ValueError(f"LLM setting with ID {setting_id} not found")
            
            # Обновляем параметры
            for key, value in kwargs.items():
                if key == "api_key" and value:
                    # Шифруем API ключ
                    value = self._encrypt_api_key(value)
                
                setattr(llm_setting, key, value)
            
            self.db.commit()
            
            return {
                "setting_id": llm_setting.setting_id,
                "provider": llm_setting.provider,
                "model_name": llm_setting.model_name,
                "is_active": llm_setting.is_active,
                "priority": llm_setting.priority
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating LLM setting: {str(e)}")
            raise
    
    def delete_llm_setting(self, setting_id: int) -> bool:
        """
        Удаление настроек ЛЛМ
        
        Args:
            setting_id: ID настроек
            
        Returns:
            True, если удаление прошло успешно, иначе False
        """
        try:
            # Получаем настройки
            llm_setting = self.db.query(LLMSetting).filter(
                LLMSetting.setting_id == setting_id
            ).first()
            
            if not llm_setting:
                raise ValueError(f"LLM setting with ID {setting_id} not found")
            
            # Удаляем настройки
            self.db.delete(llm_setting)
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting LLM setting: {str(e)}")
            return False
    
    def get_llm_settings(self) -> List[Dict]:
        """
        Получение списка настроек ЛЛМ
        
        Returns:
            Список словарей с информацией о настройках
        """
        try:
            # Получаем все настройки
            llm_settings = self.db.query(LLMSetting).all()
            
            return [
                {
                    "setting_id": setting.setting_id,
                    "provider": setting.provider,
                    "model_name": setting.model_name,
                    "endpoint_url": setting.endpoint_url,
                    "is_active": setting.is_active,
                    "priority": setting.priority
                }
                for setting in llm_settings
            ]
            
        except Exception as e:
            logger.error(f"Error getting LLM settings: {str(e)}")
            return []
    
    def get_active_llm_client(self) -> Any:
        """
        Получение активного клиента ЛЛМ
        
        Returns:
            Клиент ЛЛМ
        """
        try:
            # Получаем активные настройки с наивысшим приоритетом
            llm_setting = self.db.query(LLMSetting).filter(
                LLMSetting.is_active == True
            ).order_by(
                LLMSetting.priority.desc()
            ).first()
            
            if not llm_setting:
                # Если нет активных настроек, используем настройки из конфигурации
                if settings.GEMINI_API_KEY:
                    return self._create_gemini_client(settings.GEMINI_API_KEY)
                else:
                    raise ValueError("No active LLM settings found")
            
            # Расшифровываем API ключ
            api_key = self._decrypt_api_key(llm_setting.api_key)
            
            # Создаем клиент в зависимости от провайдера
            if llm_setting.provider == "google":
                return self._create_gemini_client(api_key)
            elif llm_setting.provider == "self-hosted":
                return self._create_self_hosted_client(api_key, llm_setting.endpoint_url, llm_setting.model_name)
            else:
                raise ValueError(f"Unsupported LLM provider: {llm_setting.provider}")
            
        except Exception as e:
            logger.error(f"Error getting active LLM client: {str(e)}")
            raise
    
    def _create_gemini_client(self, api_key: str) -> Any:
        """
        Создание клиента Gemini
        
        Args:
            api_key: API ключ
            
        Returns:
            Клиент Gemini
        """
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-pro')
    
    def _create_self_hosted_client(self, api_key: str, endpoint_url: str, model_name: str) -> Any:
        """
        Создание клиента для self-hosted модели
        
        Args:
            api_key: API ключ
            endpoint_url: URL эндпоинта
            model_name: Название модели
            
        Returns:
            Клиент self-hosted модели
        """
        # Заглушка для будущей реализации
        raise NotImplementedError("Self-hosted LLM client is not implemented yet")
    
    def test_llm_connection(self, setting_id: Optional[int] = None) -> Dict:
        """
        Тестирование подключения к ЛЛМ
        
        Args:
            setting_id: ID настроек (если None, используется активная модель)
            
        Returns:
            Словарь с результатами теста
        """
        try:
            if setting_id:
                # Получаем настройки
                llm_setting = self.db.query(LLMSetting).filter(
                    LLMSetting.setting_id == setting_id
                ).first()
                
                if not llm_setting:
                    raise ValueError(f"LLM setting with ID {setting_id} not found")
                
                # Расшифровываем API ключ
                api_key = self._decrypt_api_key(llm_setting.api_key)
                
                # Создаем клиент в зависимости от провайдера
                if llm_setting.provider == "google":
                    client = self._create_gemini_client(api_key)
                elif llm_setting.provider == "self-hosted":
                    client = self._create_self_hosted_client(api_key, llm_setting.endpoint_url, llm_setting.model_name)
                else:
                    raise ValueError(f"Unsupported LLM provider: {llm_setting.provider}")
            else:
                # Используем активную модель
                client = self.get_active_llm_client()
            
            # Тестируем подключение
            response = client.generate_content("Hello, world!")
            
            return {
                "success": True,
                "message": "Connection successful",
                "response": response.text
            }
            
        except Exception as e:
            logger.error(f"Error testing LLM connection: {str(e)}")
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "response": None
            }
    
    def categorize_event(self, event_name: str, event_description: str, event_organizer: Optional[str] = None) -> str:
        """
        Категоризация события
        
        Args:
            event_name: Название события
            event_description: Описание события
            event_organizer: Организатор события
            
        Returns:
            Категория события
        """
        try:
            # Получаем клиент ЛЛМ
            client = self.get_active_llm_client()
            
            # Формируем промпт
            prompt = f"""
            Проанализируй следующее событие и определи его категорию. Выбери одну основную категорию из списка: 
            AI/ML, Web Development, Mobile Development, Blockchain, Networking, Funding, Hardware, Cloud, Security, Data Science, DevOps, Design, Product Management, Career.

            Название события: {event_name}
            Описание события: {event_description}
            """
            
            if event_organizer:
                prompt += f"Организатор: {event_organizer}\n"
            
            prompt += "\nВерни только название категории без дополнительных пояснений."
            
            # Отправляем запрос
            response = client.generate_content(prompt)
            
            # Получаем категорию
            category = response.text.strip()
            
            # Проверяем, что категория из списка
            valid_categories = [
                "AI/ML", "Web Development", "Mobile Development", "Blockchain", 
                "Networking", "Funding", "Hardware", "Cloud", "Security", 
                "Data Science", "DevOps", "Design", "Product Management", "Career"
            ]
            
            if category not in valid_categories:
                # Если категория не из списка, выбираем наиболее близкую
                for valid_category in valid_categories:
                    if valid_category.lower() in category.lower():
                        category = valid_category
                        break
                else:
                    # Если не нашли подходящую, используем "Other"
                    category = "Other"
            
            return category
            
        except Exception as e:
            logger.error(f"Error categorizing event: {str(e)}")
            return "Other"
    
    def summarize_event(self, event_name: str, event_description: str, event_date: str, 
                       event_location: str, event_organizer: Optional[str] = None) -> str:
        """
        Создание краткого резюме события
        
        Args:
            event_name: Название события
            event_description: Описание события
            event_date: Дата события
            event_location: Место проведения события
            event_organizer: Организатор события
            
        Returns:
            Краткое резюме события
        """
        try:
            # Получаем клиент ЛЛМ
            client = self.get_active_llm_client()
            
            # Формируем промпт
            prompt = f"""
            Создай краткое резюме (не более 2-3 предложений) следующего технологического события:

            Название события: {event_name}
            Описание события: {event_description}
            Дата: {event_date}
            Место: {event_location}
            """
            
            if event_organizer:
                prompt += f"Организатор: {event_organizer}\n"
            
            prompt += "\nРезюме должно отражать основную суть события, его значимость и потенциальную ценность для участников."
            
            # Отправляем запрос
            response = client.generate_content(prompt)
            
            # Получаем резюме
            summary = response.text.strip()
            
            return summary
            
        except Exception as e:
            logger.error(f"Error summarizing event: {str(e)}")
            return "No summary available"
    
    def analyze_trends(self, events: List[Dict], start_date: str, end_date: str) -> List[Dict]:
        """
        Анализ трендов на основе событий
        
        Args:
            events: Список событий
            start_date: Дата начала периода
            end_date: Дата окончания периода
            
        Returns:
            Список трендов
        """
        try:
            # Получаем клиент ЛЛМ
            client = self.get_active_llm_client()
            
            # Формируем список событий для промпта
            events_list = ""
            for i, event in enumerate(events[:20]):  # Ограничиваем количество событий для промпта
                events_list += f"{i+1}. {event['name']} - {event['start_datetime_utc'].strftime('%Y-%m-%d')}\n"
                if event.get('description'):
                    # Ограничиваем длину описания
                    description = event['description'][:500] + "..." if len(event['description']) > 500 else event['description']
                    events_list += f"   {description}\n\n"
            
            # Формируем промпт
            prompt = f"""
            Проанализируй следующий список событий за период {start_date} - {end_date} и определи 3-5 основных трендов в технологической сфере Кремниевой долины. Для каждого тренда предоставь название и краткое описание.

            События:
            {events_list}

            Формат ответа:
            [
              {{
                "name": "Название тренда",
                "description": "Описание тренда"
              }},
              ...
            ]
            """
            
            # Отправляем запрос
            response = client.generate_content(prompt)
            
            # Получаем тренды
            trends_text = response.text.strip()
            
            # Извлекаем JSON из ответа
            try:
                # Ищем JSON в ответе
                json_match = re.search(r'\[\s*\{.*\}\s*\]', trends_text, re.DOTALL)
                if json_match:
                    trends_json = json_match.group(0)
                    trends = json.loads(trends_json)
                else:
                    # Если не нашли JSON, пробуем парсить весь ответ
                    trends = json.loads(trends_text)
            except:
                # Если не удалось распарсить JSON, создаем тренд на основе текста
                trends = [{"name": "AI and Machine Learning", "description": trends_text}]
            
            return trends
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {str(e)}")
            return [{"name": "Error", "description": f"Failed to analyze trends: {str(e)}"}]
