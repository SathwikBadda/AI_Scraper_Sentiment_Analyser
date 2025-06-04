from abc import ABC, abstractmethod
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.logger = logging.getLogger(f"{__name__}.{source_name}")
    
    @abstractmethod
    def scrape(self, query: str, limit: int = 50) -> List[Dict]:
        """
        Scrape data from the source
        Returns: List of dictionaries with keys: text, url, timestamp
        """
        pass
    
    def is_configured(self) -> bool:
        """Check if scraper is properly configured"""
        return True