import requests
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper
from typing import List, Dict
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class NewsScraper(BaseScraper):
    def __init__(self):
        super().__init__("news")
        self.base_urls = [
            'https://www.thehindu.com',
            'https://timesofindia.indiatimes.com',
            'https://www.deccanchronicle.com'
        ]
    
    def scrape(self, query: str, limit: int = 50) -> List[Dict]:
        """Scrape news articles related to Hyderabad real estate"""
        results = []
        
        try:
            # Search Google News for relevant articles
            search_query = f"{query} Hyderabad real estate news"
            google_news_url = f"https://news.google.com/rss/search?q={search_query}&hl=en-IN&gl=IN&ceid=IN:en"
            
            response = requests.get(google_news_url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'xml')
                items = soup.find_all('item')[:limit]
                
                for item in items:
                    try:
                        title = item.title.text if item.title else ""
                        description = item.description.text if item.description else ""
                        link = item.link.text if item.link else ""
                        pub_date = item.pubDate.text if item.pubDate else ""
                        
                        text_content = f"{title} {description}"
                        
                        results.append({
                            'text': text_content,
                            'url': link,
                            'timestamp': pub_date or datetime.now().isoformat()
                        })
                    except Exception as e:
                        logger.warning(f"Error parsing news item: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error scraping news: {e}")
        
        logger.info(f"Scraped {len(results)} news articles for query: {query}")
        return results