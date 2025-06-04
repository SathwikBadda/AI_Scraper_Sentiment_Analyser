from googleapiclient.discovery import build
from scrapers.base_scraper import BaseScraper
from config.config import Config
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class YouTubeScraper(BaseScraper):
    def __init__(self):
        super().__init__("youtube")
        self.api_key = Config.YOUTUBE_API_KEY
        self.youtube = None
        if self.api_key:
            try:
                self.youtube = build('youtube', 'v3', developerKey=self.api_key)
            except Exception as e:
                logger.error(f"Error initializing YouTube API: {e}")
    
    def is_configured(self) -> bool:
        return self.youtube is not None
    
    def scrape(self, query: str, limit: int = 50) -> List[Dict]:
        """Scrape YouTube comments for Hyderabad real estate videos"""
        if not self.is_configured():
            logger.warning("YouTube API not configured")
            return []
        
        results = []
        
        try:
            # Search for videos
            search_query = f"{query} Hyderabad real estate property"
            search_response = self.youtube.search().list(
                q=search_query,
                part='id,snippet',
                maxResults=10,
                type='video'
            ).execute()
            
            for video in search_response['items']:
                video_id = video['id']['videoId']
                
                try:
                    # Get comments for each video
                    comments_response = self.youtube.commentThreads().list(
                        part='snippet',
                        videoId=video_id,
                        maxResults=min(limit // 10, 20),
                        order='relevance'
                    ).execute()
                    
                    for comment in comments_response['items']:
                        comment_text = comment['snippet']['topLevelComment']['snippet']['textDisplay']
                        published_at = comment['snippet']['topLevelComment']['snippet']['publishedAt']
                        
                        results.append({
                            'text': comment_text,
                            'url': f"https://youtube.com/watch?v={video_id}",
                            'timestamp': published_at
                        })
                        
                except Exception as e:
                    logger.warning(f"Error getting comments for video {video_id}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping YouTube: {e}")
        
        logger.info(f"Scraped {len(results)} YouTube comments for query: {query}")
        return results[:limit]