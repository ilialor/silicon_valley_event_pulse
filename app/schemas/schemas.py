from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field


class SourceBase(BaseModel):
    name: str
    url: str
    type: str
    status: str = "active"


class SourceCreate(SourceBase):
    pass


class Source(SourceBase):
    source_id: int
    last_checked: Optional[datetime] = None
    relevance_score: float = 0.0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EventBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_datetime_utc: datetime
    end_datetime_utc: Optional[datetime] = None
    location_text: Optional[str] = None
    location_lat: Optional[float] = None
    location_lon: Optional[float] = None
    is_virtual: bool = False
    virtual_url: Optional[str] = None
    original_url: str
    organizer: Optional[str] = None


class EventCreate(EventBase):
    source_id: int


class EventAnalyticsBase(BaseModel):
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    summary: Optional[str] = None
    sentiment_score: Optional[float] = None
    importance_score: Optional[float] = None
    llm_model: Optional[str] = None


class EventAnalytics(EventAnalyticsBase):
    analytics_id: int
    event_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Event(EventBase):
    event_id: int
    source_id: int
    created_at: datetime
    updated_at: datetime
    analytics: Optional[EventAnalytics] = None
    source: Optional[Source] = None

    class Config:
        from_attributes = True


class EventList(BaseModel):
    total: int
    page: int
    page_size: int
    events: List[Event]


class TrendBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    event_count: int = 0
    score: float = 0.0


class TrendCreate(TrendBase):
    pass


class Trend(TrendBase):
    trend_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TrendList(BaseModel):
    trends: List[Trend]


class CategoryCount(BaseModel):
    name: str
    count: int


class CategoryList(BaseModel):
    categories: List[CategoryCount]


class LLMSettingBase(BaseModel):
    provider: str
    model_name: str
    api_key: Optional[str] = None
    endpoint_url: Optional[str] = None
    is_active: bool = False
    priority: int = 0


class LLMSettingCreate(LLMSettingBase):
    pass


class LLMSetting(LLMSettingBase):
    setting_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LLMSettingList(BaseModel):
    settings: List[LLMSetting]


class ScrapingLogBase(BaseModel):
    source_id: int
    status: str
    message: Optional[str] = None
    events_found: int = 0
    events_added: int = 0
    events_updated: int = 0
    execution_time: Optional[float] = None


class ScrapingLog(ScrapingLogBase):
    log_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ScrapingLogList(BaseModel):
    logs: List[ScrapingLog]


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str
