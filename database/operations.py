from database.db import DatabaseManager
from database.models import SentimentData
from sqlalchemy import func
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class DatabaseOperations:
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    def insert_sentiment_data(self, data: Dict) -> bool:
        """Insert sentiment data into database"""
        session = self.db_manager.get_session()
        try:
            sentiment_record = SentimentData(**data)
            session.add(sentiment_record)
            session.commit()
            logger.info(f"Inserted sentiment data for location: {data['location']}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error inserting sentiment data: {e}")
            return False
        finally:
            self.db_manager.close_session(session)
    
    def get_sentiment_by_location(self, location: str) -> List[Dict]:
        """Get all sentiment data for a specific location"""
        session = self.db_manager.get_session()
        try:
            results = session.query(SentimentData).filter(
                SentimentData.location.ilike(f'%{location}%')
            ).all()
            
            data = []
            for result in results:
                data.append({
                    'id': result.id,
                    'source': result.source,
                    'location': result.location,
                    'raw_text': result.raw_text,
                    'clean_text': result.clean_text,
                    'sentiment': result.sentiment,
                    'reason': result.reason,
                    'score': result.score,
                    'timestamp': result.timestamp
                })
            return data
        except Exception as e:
            logger.error(f"Error fetching sentiment data: {e}")
            return []
        finally:
            self.db_manager.close_session(session)
    
    def get_sentiment_summary(self, location: str) -> Dict:
        """Get sentiment summary for a location"""
        session = self.db_manager.get_session()
        try:
            total_count = session.query(SentimentData).filter(
                SentimentData.location.ilike(f'%{location}%')
            ).count()
            
            sentiment_counts = session.query(
                SentimentData.sentiment,
                func.count(SentimentData.sentiment).label('count')
            ).filter(
                SentimentData.location.ilike(f'%{location}%')
            ).group_by(SentimentData.sentiment).all()
            
            source_counts = session.query(
                SentimentData.source,
                func.count(SentimentData.source).label('count')
            ).filter(
                SentimentData.location.ilike(f'%{location}%')
            ).group_by(SentimentData.source).all()
            
            return {
                'total_mentions': total_count,
                'sentiment_distribution': dict(sentiment_counts),
                'source_distribution': dict(source_counts)
            }
        except Exception as e:
            logger.error(f"Error fetching sentiment summary: {e}")
            return {}
        finally:
            self.db_manager.close_session(session)