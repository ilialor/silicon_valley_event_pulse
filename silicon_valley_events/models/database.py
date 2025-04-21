
from datetime import datetime
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.pool import QueuePool

# Create base class for declarative models
Base = declarative_base()

# Association table for event tags
event_tags = Table(
    'event_tags',
    Base.metadata,
    Column('event_id', Integer, ForeignKey('events.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

class EventModel(Base):
    """Database model for events"""
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True)
    external_id = Column(String, unique=True)
    title = Column(String)
    description = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime, nullable=True)
    location = Column(String)
    url = Column(String)
    source = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with tags
    tags = relationship('TagModel', secondary=event_tags, back_populates='events')

class TagModel(Base):
    """Database model for tags"""
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    events = relationship('EventModel', secondary=event_tags, back_populates='tags')

class EventStorage:
    """Storage class for managing events in the database"""
    def __init__(self, db_url: str = "sqlite:///events.db"):
        self.engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def get_or_create_tag(self, session: Session, tag_name: str) -> TagModel:
        """Get existing tag or create new one"""
        tag = session.query(TagModel).filter_by(name=tag_name).first()
        if not tag:
            tag = TagModel(name=tag_name)
            session.add(tag)
            session.flush()
        return tag
    
    def save_event(self, event: 'Event') -> None:
        """Save or update an event in the database"""
        with self.Session() as session:
            try:
                # Check if event already exists
                existing_event = session.query(EventModel).filter_by(
                    external_id=event.id
                ).first()
                
                if existing_event:
                    # Update existing event
                    existing_event.title = event.title
                    existing_event.description = event.description
                    existing_event.start_time = event.start_time
                    existing_event.end_time = event.end_time
                    existing_event.location = event.location
                    existing_event.url = event.url
                    existing_event.source = event.source
                else:
                    # Create new event
                    db_event = EventModel(
                        external_id=event.id,
                        title=event.title,
                        description=event.description,
                        start_time=event.start_time,
                        end_time=event.end_time,
                        location=event.location,
                        url=event.url,
                        source=event.source
                    )
                    session.add(db_event)
                    
                    # Add tags
                    if event.tags:
                        for tag_name in event.tags:
                            tag = self.get_or_create_tag(session, tag_name)
                            db_event.tags.append(tag)
                
                session.commit()
            except Exception as e:
                session.rollback()
                raise e
    
    def get_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        source: Optional[str] = None,
        tag: Optional[str] = None
    ) -> List[EventModel]:
        """Retrieve events with optional filtering"""
        with self.Session() as session:
            query = session.query(EventModel)
            
            if start_date:
                query = query.filter(EventModel.start_time >= start_date)
            if end_date:
                query = query.filter(EventModel.start_time <= end_date)
            if source:
                query = query.filter(EventModel.source == source)
            if tag:
                query = query.join(EventModel.tags).filter(TagModel.name == tag)
            
            return query.all()
