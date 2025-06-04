import snscrape.modules.twitter as sntwitter
from scrapers.base_scraper import BaseScraper
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class TwitterScraper(BaseScraper):
    def __init__(self):
        super().__init__("twitter")
    
    def scrape(self, query: str, limit: int = 50) -> List[Dict]:
        """Scrape Twitter posts about Hyderabad real estate"""
        results = []
        
        try:
            search_query = f"{query} Hyderabad real estate property OR flat OR apartment"
            
            # Use snscrape to get tweets
            tweets = sntwitter.TwitterSearchScraper(search_query).get_items()
            
            count = 0
            for tweet in tweets:
                if count >= limit:
                    break
                    
                try:
                    results.append({
                        'text': tweet.rawContent,
                        'url': tweet.url,
                        'timestamp': tweet.date.isoformat()
                    })
                    count += 1
                except Exception as e:
                    logger.warning(f"Error processing tweet: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Twitter: {e}")
        
        logger.info(f"Scraped {len(results)} tweets for query: {query}")
        return results