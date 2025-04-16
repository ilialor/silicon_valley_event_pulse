from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.api.endpoints import events, llm
from app.core.config import settings
from app.db.session import engine, Base, get_db

# Создаем таблицы в базе данных
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Silicon Valley Event Pulse API",
    description="API для системы поиска и анализа событий в Кремниевой долине",
    version="0.1.0",
)

# Настройка CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Подключаем роутеры
app.include_router(events.router, prefix=f"{settings.API_V1_STR}/events", tags=["events"])
app.include_router(llm.router, prefix=f"{settings.API_V1_STR}/llm", tags=["llm"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Silicon Valley Event Pulse API"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        # Проверяем подключение к базе данных
        db.execute("SELECT 1")
        return {"status": "ok", "message": "Service is healthy"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
