from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from app.db.session import Base


class Source(Base):
    __tablename__ = "sources"

    source_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    url = Column(String(512), nullable=False)
    type = Column(String(50), nullable=False)  # 'meetup', 'eventbrite', 'techcrunch', etc.
    status = Column(String(50), nullable=False, default="active")  # 'active', 'inactive', 'error'
    last_checked = Column(DateTime(timezone=True), nullable=True)
    relevance_score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    events = relationship("Event", back_populates="source")
    scraping_logs = relationship("ScrapingLog", back_populates="source")


class Event(Base):
    __tablename__ = "events"

    event_id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.source_id"))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_datetime_utc = Column(DateTime(timezone=True), nullable=False)
    end_datetime_utc = Column(DateTime(timezone=True), nullable=True)
    location_text = Column(String(512), nullable=True)
    location_lat = Column(Float, nullable=True)
    location_lon = Column(Float, nullable=True)
    is_virtual = Column(Boolean, default=False)
    virtual_url = Column(String(512), nullable=True)
    original_url = Column(String(512), nullable=False)
    organizer = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    source = relationship("Source", back_populates="events")
    analytics = relationship("EventAnalytics", back_populates="event", uselist=False)
    trends = relationship("TrendEvent", back_populates="event")


class EventAnalytics(Base):
    __tablename__ = "event_analytics"

    analytics_id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.event_id", ondelete="CASCADE"))
    category = Column(String(100), nullable=True)
    tags = Column(ARRAY(String), nullable=True)
    summary = Column(Text, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    importance_score = Column(Float, nullable=True)
    llm_model = Column(String(100), nullable=True)  # 'gemini', 'llama', etc.
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    event = relationship("Event", back_populates="analytics")


class Trend(Base):
    __tablename__ = "trends"

    trend_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    event_count = Column(Integer, default=0)
    score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    events = relationship("TrendEvent", back_populates="trend")


class TrendEvent(Base):
    __tablename__ = "trend_events"

    trend_id = Column(Integer, ForeignKey("trends.trend_id", ondelete="CASCADE"), primary_key=True)
    event_id = Column(Integer, ForeignKey("events.event_id", ondelete="CASCADE"), primary_key=True)
    relevance_score = Column(Float, default=0.0)

    # Relationships
    trend = relationship("Trend", back_populates="events")
    event = relationship("Event", back_populates="trends")


class LLMSetting(Base):
    __tablename__ = "llm_settings"

    setting_id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(100), nullable=False)  # 'google', 'openai', 'anthropic', 'self-hosted', etc.
    model_name = Column(String(100), nullable=False)  # 'gemini-pro', 'llama-3', etc.
    api_key = Column(String(512), nullable=True)  # Зашифрованный ключ API
    endpoint_url = Column(String(512), nullable=True)  # Для self-hosted моделей
    is_active = Column(Boolean, default=False)
    priority = Column(Integer, default=0)  # Приоритет использования, если активно несколько моделей
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class ScrapingLog(Base):
    __tablename__ = "scraping_logs"

    log_id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.source_id"))
    status = Column(String(50), nullable=False)  # 'success', 'error', 'warning'
    message = Column(Text, nullable=True)
    events_found = Column(Integer, default=0)
    events_added = Column(Integer, default=0)
    events_updated = Column(Integer, default=0)
    execution_time = Column(Float, nullable=True)  # в секундах
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    source = relationship("Source", back_populates="scraping_logs")
