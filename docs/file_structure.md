# Структура файлов Silicon Valley Event Pulse

```
silicon_valley_event_pulse/
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── endpoints/
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py
│   ├── db/
│   │   ├── __init__.py
│   │   └── session.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── models.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── schemas.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── analytics/
│   │   ├── data_processor.py
│   │   ├── llm/
│   │   └── scraping/
│   └── utils/
│       └── __init__.py
├── dist/
├── tests/
│   ├── test_api_endpoints.py
│   ├── test_gemini_integration.py
│   ├── test_llm_integration.py
│   ├── test_models.py
│   ├── test_scrapers.py
│   └── test_ui.py
├── calendar.html
├── deployment_guide.md
├── event_details.html
├── index.html
├── llm_settings.html
├── requirements.txt
├── run_demo.sh
├── trends.html
├── user_guide.md
└── README.md
```

## Описание ключевых файлов и папок

- **app/** — основной код приложения.
  - **api/** — обработка HTTP-запросов и маршрутизация.
  - **core/** — настройки и конфигурация.
  - **db/** — подключение и работа с базой данных.
  - **models/** — определение ORM-моделей.
  - **schemas/** — схемы данных для валидации и сериализации.
  - **services/** — бизнес-логика, аналитика, интеграция с LLM, парсинг.
  - **utils/** — вспомогательные функции.
  - `main.py` — точка входа приложения.
- **dist/** — артефакты сборки.
- **tests/** — тесты для проверки различных компонентов.
- **HTML-файлы** — интерфейс пользователя.
- **requirements.txt** — список зависимостей проекта.
- **deployment_guide.md** — руководство по развертыванию.
- **user_guide.md** — руководство пользователя.
- **README.md** — основная информация о проекте.

---
Все изменения структуры должны сопровождаться обновлением этого файла.
