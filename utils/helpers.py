import os
import json
import re
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
import logging
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)

class FileHelper:
    """File and directory operations helper"""
    
    @staticmethod
    def ensure_directory_exists(directory: Union[str, Path]) -> None:
        """Ensure directory exists, create if not"""
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path}")
    
    @staticmethod
    def save_json(data: Dict[Any, Any], filepath: Union[str, Path]) -> bool:
        """Save data to JSON file"""
        try:
            filepath = Path(filepath)
            FileHelper.ensure_directory_exists(filepath.parent)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str, ensure_ascii=False)
            
            logger.info(f"Saved JSON data to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error saving JSON to {filepath}: {e}")
            return False
    
    @staticmethod
    def load_json(filepath: Union[str, Path]) -> Dict[Any, Any]:
        """Load data from JSON file"""
        try:
            filepath = Path(filepath)
            if not filepath.exists():
                logger.warning(f"JSON file not found: {filepath}")
                return {}
                
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Loaded JSON data from {filepath}")
            return data
        except Exception as e:
            logger.error(f"Error loading JSON from {filepath}: {e}")
            return {}
    
    @staticmethod
    def save_csv(df: pd.DataFrame, filepath: Union[str, Path]) -> bool:
        """Save DataFrame to CSV file"""
        try:
            filepath = Path(filepath)
            FileHelper.ensure_directory_exists(filepath.parent)
            
            df.to_csv(filepath, index=False, encoding='utf-8')
            logger.info(f"Saved CSV data to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error saving CSV to {filepath}: {e}")
            return False

class DateTimeHelper:
    """Date and time operations helper"""
    
    @staticmethod
    def format_timestamp(timestamp: Union[str, datetime, int, float]) -> str:
        """Format timestamp to readable string"""
        try:
            if isinstance(timestamp, str):
                # Try to parse string timestamp
                try:
                    dt = pd.to_datetime(timestamp)
                    return dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    return timestamp
            elif isinstance(timestamp, datetime):
                return timestamp.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(timestamp, (int, float)):
                # Unix timestamp
                dt = datetime.fromtimestamp(timestamp)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            else:
                return str(timestamp)
        except Exception as e:
            logger.error(f"Error formatting timestamp: {e}")
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    @staticmethod
    def get_date_range(days_back: int = 7) -> tuple:
        """Get date range for filtering"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        return start_date, end_date
    
    @staticmethod
    def is_recent(timestamp: Union[str, datetime], hours: int = 24) -> bool:
        """Check if timestamp is recent (within specified hours)"""
        try:
            if isinstance(timestamp, str):
                dt = pd.to_datetime(timestamp)
            elif isinstance(timestamp, datetime):
                dt = timestamp
            else:
                return False
            
            cutoff = datetime.now() - timedelta(hours=hours)
            return dt.replace(tzinfo=None) >= cutoff
        except:
            return False

class DataHelper:
    """Data processing and analysis helper"""
    
    @staticmethod
    def calculate_sentiment_score(positive: int, negative: int, neutral: int) -> float:
        """Calculate overall sentiment score"""
        total = positive + negative + neutral
        if total == 0:
            return 0.0
        
        # Weight positive as +1, negative as -1, neutral as 0
        score = (positive - negative) / total
        return round(score, 3)
    
    @staticmethod
    def get_sentiment_label(score: float) -> str:
        """Convert sentiment score to label"""
        if score > 0.1:
            return "Positive"
        elif score < -0.1:
            return "Negative"
        else:
            return "Neutral"
    
    @staticmethod
    def clean_text_basic(text: str) -> str:
        """Basic text cleaning"""
        if not text:
            return ""
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\!\?\,\;\:]', '', text)
        
        return text.strip()
    
    @staticmethod
    def extract_keywords_simple(text: str, top_k: int = 10) -> List[str]:
        """Simple keyword extraction using frequency"""
        if not text:
            return []
        
        # Common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we',
            'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her',
            'its', 'our', 'their'
        }
        
        # Extract words
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter stop words and short words
        words = [word for word in words if word not in stop_words and len(word) > 3]
        
        # Count frequency
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top k
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:top_k]]
    
    @staticmethod
    def filter_dataframe(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """Filter DataFrame based on various criteria"""
        if df.empty:
            return df
        
        filtered_df = df.copy()
        
        try:
            # Date range filter
            if 'date_range' in filters and filters['date_range']:
                start_date, end_date = filters['date_range']
                filtered_df['timestamp'] = pd.to_datetime(filtered_df['timestamp'])
                mask = (filtered_df['timestamp'].dt.date >= start_date) & \
                       (filtered_df['timestamp'].dt.date <= end_date)
                filtered_df = filtered_df[mask]
            
            # Source filter
            if 'source_filters' in filters:
                active_sources = [source for source, active in filters['source_filters'].items() if active]
                if active_sources:
                    filtered_df = filtered_df[filtered_df['source'].isin(active_sources)]
            
            # Sentiment filter
            if 'sentiment_filters' in filters:
                sentiment_map = {'positive': 'Positive', 'negative': 'Negative', 'neutral': 'Neutral'}
                active_sentiments = [sentiment_map[sent] for sent, active in filters['sentiment_filters'].items() if active]
                if active_sentiments:
                    filtered_df = filtered_df[filtered_df['sentiment'].isin(active_sentiments)]
            
            return filtered_df
            
        except Exception as e:
            logger.error(f"Error filtering DataFrame: {e}")
            return df

class ValidationHelper:
    """Data validation helper"""
    
    @staticmethod
    def validate_api_key(api_key: str, api_name: str = "API") -> bool:
        """Validate API key format"""
        if not api_key or not isinstance(api_key, str):
            return False
        
        # Basic validation - check if it's not empty and has reasonable length
        api_key = api_key.strip()
        if len(api_key) < 10:
            return False
        
        # Check for common placeholder values
        invalid_values = ['your_api_key', 'api_key_here', 'replace_with_your_key', 'none', 'null']
        if api_key.lower() in invalid_values:
            return False
        
        return True
    
    @staticmethod
    def validate_location(location: str, valid_locations: List[str]) -> bool:
        """Validate if location is in the list of valid locations"""
        if not location:
            return False
        
        location_lower = location.lower()
        valid_locations_lower = [loc.lower() for loc in valid_locations]
        
        return location_lower in valid_locations_lower
    
    @staticmethod
    def validate_sentiment_data(data: Dict[str, Any]) -> bool:
        """Validate sentiment data structure"""
        required_fields = ['source', 'location', 'raw_text', 'clean_text', 'sentiment', 'score']
        
        if not isinstance(data, dict):
            return False
        
        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate sentiment value
        if data['sentiment'] not in ['Positive', 'Negative', 'Neutral']:
            logger.error(f"Invalid sentiment value: {data['sentiment']}")
            return False
        
        # Validate score range
        try:
            score = float(data['score'])
            if score < -1 or score > 1:
                logger.error(f"Score out of range [-1, 1]: {score}")
                return False
        except (ValueError, TypeError):
            logger.error(f"Invalid score value: {data['score']}")
            return False
        
        return True

class CacheHelper:
    """Caching operations helper"""
    
    @staticmethod
    def generate_cache_key(*args) -> str:
        """Generate cache key from arguments"""
        key_string = "_".join(str(arg) for arg in args)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    @staticmethod
    def is_cache_valid(cache_file: Union[str, Path], max_age_minutes: int = 30) -> bool:
        """Check if cache file is still valid"""
        try:
            cache_path = Path(cache_file)
            if not cache_path.exists():
                return False
            
            file_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
            return file_age < timedelta(minutes=max_age_minutes)
            
        except Exception as e:
            logger.error(f"Error checking cache validity: {e}")
            return False

class ConfigHelper:
    """Configuration management helper"""
    
    @staticmethod
    def load_config(config_path: Union[str, Path] = ".env") -> Dict[str, str]:
        """Load configuration from .env file"""
        config = {}
        config_path = Path(config_path)
        
        if not config_path.exists():
            logger.warning(f"Config file not found: {config_path}")
            return config
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip().strip('"\'')
            
            logger.info(f"Loaded configuration from {config_path}")
            return config
            
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return config
    
    @staticmethod
    def validate_config(config: Dict[str, str], required_keys: List[str]) -> Dict[str, bool]:
        """Validate configuration against required keys"""
        validation_result = {}
        
        for key in required_keys:
            value = config.get(key, "")
            validation_result[key] = ValidationHelper.validate_api_key(value, key)
        
        return validation_result

class URLHelper:
    """URL and web-related helper functions"""
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check if URL is valid"""
        if not url:
            return False
        
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return url_pattern.match(url) is not None
    
    @staticmethod
    def extract_domain(url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return ""
    
    @staticmethod
    def clean_url(url: str) -> str:
        """Clean and normalize URL"""
        if not url:
            return ""
        
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        return url