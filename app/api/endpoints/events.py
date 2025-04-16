from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime, timedelta

from app.db.session import get_db
from app.models import models
from app.schemas import schemas

router = APIRouter()

@router.get("/events", response_model=schemas.EventList)
def get_events(
    db: Session = Depends(get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category: Optional[str] = None,
    is_virtual: Optional[bool] = None,
    location: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    Получение списка событий с возможностью фильтрации
    """
    # Базовый запрос
    query = db.query(models.Event).join(
        models.Source, models.Event.source_id == models.Source.source_id
    ).outerjoin(
        models.EventAnalytics, models.Event.event_id == models.EventAnalytics.event_id
    )
    
    # Применяем фильтры
    if start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        query = query.filter(models.Event.start_datetime_utc >= start_datetime)
    
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        query = query.filter(models.Event.start_datetime_utc <= end_datetime)
    
    if category:
        query = query.filter(models.EventAnalytics.category == category)
    
    if is_virtual is not None:
        query = query.filter(models.Event.is_virtual == is_virtual)
    
    if location:
        query = query.filter(models.Event.location_text.ilike(f"%{location}%"))
    
    if search:
        query = query.filter(
            (models.Event.name.ilike(f"%{search}%")) | 
            (models.Event.description.ilike(f"%{search}%"))
        )
    
    # Сортировка по дате начала
    query = query.order_by(models.Event.start_datetime_utc)
    
    # Подсчет общего количества
    total = query.count()
    
    # Пагинация
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    # Получение результатов
    events = query.all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "events": events
    }

@router.get("/events/{event_id}", response_model=schemas.Event)
def get_event(event_id: int, db: Session = Depends(get_db)):
    """
    Получение информации о конкретном событии
    """
    event = db.query(models.Event).filter(models.Event.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.get("/analytics/categories", response_model=schemas.CategoryList)
def get_categories(
    db: Session = Depends(get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    """
    Получение списка категорий событий с количеством событий в каждой категории
    """
    # Базовый запрос
    query = db.query(
        models.EventAnalytics.category,
        db.func.count(models.EventAnalytics.event_id).label("count")
    ).join(
        models.Event, models.EventAnalytics.event_id == models.Event.event_id
    ).group_by(
        models.EventAnalytics.category
    )
    
    # Применяем фильтры по дате
    if start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        query = query.filter(models.Event.start_datetime_utc >= start_datetime)
    
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        query = query.filter(models.Event.start_datetime_utc <= end_datetime)
    
    # Получение результатов
    categories = query.all()
    
    return {
        "categories": [{"name": category, "count": count} for category, count in categories if category]
    }

@router.get("/analytics/trends", response_model=schemas.TrendList)
def get_trends(
    db: Session = Depends(get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    """
    Получение списка трендов
    """
    # Базовый запрос
    query = db.query(models.Trend)
    
    # Применяем фильтры по дате
    if start_date:
        query = query.filter(models.Trend.start_date >= start_date)
    
    if end_date:
        query = query.filter(models.Trend.end_date <= end_date)
    
    # Сортировка по score (от большего к меньшему)
    query = query.order_by(models.Trend.score.desc())
    
    # Получение результатов
    trends = query.all()
    
    return {"trends": trends}

@router.get("/analytics/trends/{trend_id}/events", response_model=List[schemas.Event])
def get_trend_events(trend_id: int, db: Session = Depends(get_db)):
    """
    Получение событий, связанных с трендом
    """
    trend = db.query(models.Trend).filter(models.Trend.trend_id == trend_id).first()
    if not trend:
        raise HTTPException(status_code=404, detail="Trend not found")
    
    events = db.query(models.Event).join(
        models.TrendEvent, models.Event.event_id == models.TrendEvent.event_id
    ).filter(
        models.TrendEvent.trend_id == trend_id
    ).order_by(
        models.TrendEvent.relevance_score.desc()
    ).all()
    
    return events

@router.get("/sources", response_model=List[schemas.Source])
def get_sources(db: Session = Depends(get_db)):
    """
    Получение списка источников данных
    """
    sources = db.query(models.Source).all()
    return sources

@router.get("/scraping/logs", response_model=schemas.ScrapingLogList)
def get_scraping_logs(
    db: Session = Depends(get_db),
    source_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    Получение логов сбора данных
    """
    # Базовый запрос
    query = db.query(models.ScrapingLog)
    
    # Применяем фильтры
    if source_id:
        query = query.filter(models.ScrapingLog.source_id == source_id)
    
    if status:
        query = query.filter(models.ScrapingLog.status == status)
    
    # Сортировка по дате создания (от новых к старым)
    query = query.order_by(models.ScrapingLog.created_at.desc())
    
    # Пагинация
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    # Получение результатов
    logs = query.all()
    
    return {"logs": logs}
