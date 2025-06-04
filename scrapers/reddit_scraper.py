import praw
from scrapers.base_scraper import BaseScraper
from config.config import Config
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class RedditScraper(BaseScraper):
    def __init__(self):
        super().__init__("reddit")
        self.reddit = None
        if all([Config.REDDIT_CLIENT_ID, Config.REDDIT_CLIENT_SECRET]):
            try:
                self.reddit = praw.Reddit(
                    client_id=Config.REDDIT_CLIENT_ID,
                    client_secret=Config.REDDIT_CLIENT_SECRET,
                    user_agent=Config.REDDIT_USER_AGENT
                )
            except Exception as e:
                logger.error(f"Error initializing Reddit API: {e}")
    
    def is_configured(self) -> bool:
        return self.reddit is not None
    
    def scrape(self, query: str, limit: int = 50) -> List[Dict]:
        """Scrape Reddit posts and comments about Hyderabad real estate"""
        if not self.is_configured():
            logger.warning("Reddit API not configured")
            return []
        
        results = []
        
        try:
            # Search in relevant subreddits
            subreddits = ['hyderabad', 'india', 'IndiaInvestments', 'RealEstate']
            search_query = f"{query} real estate property"
            
            for subreddit_name in subreddits:
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)
                    
                    # Search posts
                    for submission in subreddit.search(search_query, limit=limit//len(subreddits)):
                        # Add post title and content
                        post_text = f"{submission.title} {submission.selftext}"
                        results.append({
                            'text': post_text,
                            'url': f"https://reddit.com{submission.permalink}",
                            'timestamp': submission.created_utc
                        })
                        
                        # Add top comments
                        submission.comments.replace_more(limit=0)
                        for comment in submission.comments[:5]:
                            if hasattr(comment, 'body') and len(comment.body) > 20:
                                results.append({
                                    'text': comment.body,
                                    'url': f"https://reddit.com{submission.permalink}",
                                    'timestamp': comment.created_utc
                                })
                                
                except Exception as e:
                    logger.warning(f"Error scraping subreddit {subreddit_name}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Reddit: {e}")
        
        logger.info(f"Scraped {len(results)} Reddit posts/comments for query: {query}")
        return results[:limit]