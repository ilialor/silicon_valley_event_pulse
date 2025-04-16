# Инструкция по развертыванию Silicon Valley Event Pulse

Данный документ содержит инструкции по развертыванию системы "Silicon Valley Event Pulse" - платформы для поиска и анализа технологических событий в Кремниевой долине.

## Требования к системе

- Python 3.8 или выше
- PostgreSQL 12 или выше
- Node.js 14 или выше (для запуска фронтенда)
- Доступ к интернету для сбора данных о событиях и взаимодействия с API языковых моделей

## Шаг 1: Клонирование репозитория

```bash
git clone https://github.com/yourusername/silicon_valley_event_pulse.git
cd silicon_valley_event_pulse
```

## Шаг 2: Настройка виртуального окружения Python

```bash
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Шаг 3: Настройка базы данных PostgreSQL

1. Создайте базу данных PostgreSQL:

```bash
sudo -u postgres psql
CREATE DATABASE event_pulse;
CREATE USER event_pulse_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE event_pulse TO event_pulse_user;
\q
```

2. Обновите конфигурацию базы данных в файле `app/core/config.py`:

```python
DATABASE_URL = "postgresql://event_pulse_user:your_password@localhost/event_pulse"
```

3. Инициализируйте базу данных:

```bash
python scripts/init_db.py
```

## Шаг 4: Настройка API ключей для языковых моделей

1. Получите API ключ для Google Gemini API:
   - Перейдите на [Google AI Studio](https://ai.google.dev/)
   - Создайте проект и получите API ключ
   
2. Добавьте API ключ в файл `.env` в корневой директории проекта:

```
GEMINI_API_KEY=your_gemini_api_key
```

## Шаг 5: Запуск бэкенда

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Бэкенд будет доступен по адресу: http://localhost:8000

## Шаг 6: Запуск фронтенда

Для локальной разработки вы можете использовать простой HTTP-сервер для обслуживания статических файлов:

```bash
cd silicon_valley_event_pulse
python -m http.server 8080
```

Фронтенд будет доступен по адресу: http://localhost:8080

## Шаг 7: Настройка сбора данных о событиях

Для автоматического сбора данных о событиях настройте cron-задачу:

```bash
crontab -e
```

Добавьте следующую строку для запуска сбора данных каждый день в 2:00:

```
0 2 * * * cd /path/to/silicon_valley_event_pulse && /path/to/venv/bin/python scripts/collect_events.py >> /path/to/logs/collect_events.log 2>&1
```

## Шаг 8: Настройка производственного окружения (опционально)

Для производственного развертывания рекомендуется:

1. Использовать Nginx в качестве обратного прокси-сервера
2. Настроить SSL-сертификаты для HTTPS
3. Использовать Gunicorn для запуска FastAPI приложения
4. Настроить мониторинг и логирование

Пример конфигурации Nginx:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        root /path/to/silicon_valley_event_pulse;
        index index.html;
        try_files $uri $uri/ =404;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Устранение неполадок

### Проблемы с подключением к базе данных

Убедитесь, что:
- PostgreSQL запущен и работает
- Учетные данные в конфигурации корректны
- Пользователь имеет необходимые права доступа

### Проблемы с API ключами

Если возникают ошибки при взаимодействии с Gemini API:
- Проверьте правильность API ключа
- Убедитесь, что ключ активирован и имеет достаточные квоты
- Проверьте подключение к интернету

### Проблемы с фронтендом

Если страницы не отображаются корректно:
- Проверьте консоль браузера на наличие ошибок JavaScript
- Убедитесь, что все пути к ресурсам корректны
- Проверьте, что API endpoints доступны и возвращают ожидаемые данные

## Контакты для поддержки

При возникновении проблем с развертыванием или использованием системы, пожалуйста, обращайтесь:
- Email: support@eventpulse.example.com
- GitHub Issues: https://github.com/yourusername/silicon_valley_event_pulse/issues
