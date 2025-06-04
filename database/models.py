from sqlalchemy import Column, Integer, String, Text, Float, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class SentimentData(Base):
    __tablename__ = 'sentiment_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False)
    location = Column(String(100), nullable=False)
    raw_text = Column(Text, nullable=False)
    clean_text = Column(Text, nullable=False)
    sentiment = Column(String(20), nullable=False)  # Positive/Negative/Neutral
    reason = Column(Text)
    score = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<SentimentData(location='{self.location}', sentiment='{self.sentiment}', score={self.score})>"