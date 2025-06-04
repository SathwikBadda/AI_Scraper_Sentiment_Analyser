# config/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///real_estate_sentiment.db')
    
    # Reddit API Configuration
    REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
    REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
    REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT', 'RealEstateSentimentBot/1.0')
    
    # YouTube API Configuration
    YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
    
    # Instagram API Configuration (Meta Graph API)
    INSTAGRAM_ACCESS_TOKEN = os.getenv('INSTAGRAM_ACCESS_TOKEN')
    INSTAGRAM_USER_ID = os.getenv('INSTAGRAM_USER_ID')  # Your Instagram Business Account ID
    INSTAGRAM_APP_ID = os.getenv('INSTAGRAM_APP_ID')
    INSTAGRAM_APP_SECRET = os.getenv('INSTAGRAM_APP_SECRET')
    
    # Claude API Configuration
    CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
    
    # Perplexity AI Configuration
    PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
    
    # Hyderabad Localities for Location Extraction
    HYDERABAD_LOCALITIES = [
        'Kondapur', 'Gachibowli', 'Madhapur', 'Hitech City', 'Financial District',
        'Banjara Hills', 'Jubilee Hills', 'Kukatpally', 'Miyapur', 'Begumpet',
        'Secunderabad', 'Ameerpet', 'Somajiguda', 'Abids', 'Charminar',
        'Dilsukhnagar', 'Uppal', 'Kompally', 'Bachupally', 'Nizampet',
        'Manikonda', 'Kokapet', 'Nanakramguda', 'Raidurg', 'Chandanagar',
        'Yellahanka', 'Shamshabad', 'Patancheru', 'Sangareddy', 'Medchal',
        'LB Nagar', 'Vanasthalipuram', 'Hayathnagar', 'Ghatkesar', 'Keesara',
        'Shamirpet', 'Malkajgiri', 'Alwal', 'Bowenpally', 'Trimulgherry',
        'Yapral', 'Sainikpuri', 'AS Rao Nagar', 'ECIL', 'Nagole',
        'Boduppal', 'Ramanthapur', 'Tarnaka', 'Himayatnagar', 'Narayanguda'
    ]
    
    # Sentiment Analysis Configuration
    SENTIMENT_THRESHOLDS = {
        'POSITIVE_THRESHOLD': 0.1,
        'NEGATIVE_THRESHOLD': -0.1,
        'HIGH_CONFIDENCE_THRESHOLD': 0.7
    }
    
    # Rate Limiting Configuration
    RATE_LIMITS = {
        'REDDIT_REQUESTS_PER_MINUTE': 60,
        'YOUTUBE_REQUESTS_PER_DAY': 10000,
        'INSTAGRAM_REQUESTS_PER_HOUR': 200,
        'CLAUDE_REQUESTS_PER_MINUTE': 50,
        'PERPLEXITY_REQUESTS_PER_MINUTE': 20,
        'SEARCH_REQUESTS_PER_DAY': 100
    }
    
    # Scraping Configuration
    SCRAPING_CONFIG = {
        'DEFAULT_LIMIT': 50,
        'MAX_TEXT_LENGTH': 1000,
        'MIN_TEXT_LENGTH': 20,
        'REQUEST_TIMEOUT': 30,
        'RETRY_ATTEMPTS': 3,
        'RETRY_DELAY': 2
    }
    
    # Analysis Configuration
    ANALYSIS_CONFIG = {
        'CLAUDE_MODEL': 'claude-3-sonnet-20240229',
        'CLAUDE_MAX_TOKENS': 2000,
        'PERPLEXITY_MODEL': 'llama-3.1-sonar-small-128k-online',
        'BATCH_SIZE': 10,
        'CACHE_EXPIRY_HOURS': 24
    }
    
    # Instagram-specific Configuration
    INSTAGRAM_CONFIG = {
        'REAL_ESTATE_HASHTAGS': [
            'hyderabadrealstate', 'hyderabadproperty', 'realestatehyderabad',
            'propertyinhyderabad', 'hyderabadflats', 'hyderabadapartments',
            'hyderabadhomes', 'hyderabadinvestment', 'hyderabadrealty',
            'propertydealshyderabad', 'hyderabadproperties', 'realestatedeals'
        ],
        'REAL_ESTATE_ACCOUNTS': [
            'hyderabadrealestate', 'propertyinhyderabad', 'hyderabadproperties',
            'realestatehyderabad', 'hyderabadflats', 'propertydealshyderabad',
            'hyderabadrealty', 'realestatetelangana', 'propertyguruhyderabad'
        ],
        'LOCATION_HASHTAG_TEMPLATES': [
            '{location}realestate', '{location}property', '{location}apartments',
            '{location}flats', '{location}homes', 'hyderabad{location}',
            '{location}investment', '{location}realty'
        ]
    }
    
    # Logging Configuration
    LOGGING_CONFIG = {
        'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
        'LOG_FILE': os.getenv('LOG_FILE', 'real_estate_sentiment.log'),
        'MAX_LOG_SIZE': 10 * 1024 * 1024,  # 10MB
        'BACKUP_COUNT': 5
    }
    
    @classmethod
    def validate_config(cls):
        """Validate configuration and return status of each component"""
        validation_results = {
            'database': bool(cls.DATABASE_URL),
            'reddit': bool(cls.REDDIT_CLIENT_ID and cls.REDDIT_CLIENT_SECRET),
            'youtube': bool(cls.YOUTUBE_API_KEY),
            'instagram': bool(cls.INSTAGRAM_ACCESS_TOKEN and cls.INSTAGRAM_USER_ID),
            'claude': bool(cls.CLAUDE_API_KEY)
        }
        
        return validation_results
    
    @classmethod
    def get_missing_configs(cls):
        """Get list of missing configuration items"""
        validation = cls.validate_config()
        missing = [component for component, is_valid in validation.items() if not is_valid]
        return missing
    
    @classmethod
    def is_fully_configured(cls):
        """Check if all critical components are configured"""
        validation = cls.validate_config()
        # Database, Claude, and at least one scraper should be configured
        return validation['database'] and validation['claude'] and any([
            validation['reddit'], validation['youtube'], 
            validation['instagram']
        ])
    
    @classmethod
    def get_configuration_guide(cls):
        """Get configuration guide for missing components"""
        missing = cls.get_missing_configs()
        
        guides = {
            'reddit': {
                'description': 'Reddit API for scraping real estate discussions',
                'steps': [
                    '1. Go to https://www.reddit.com/prefs/apps',
                    '2. Create a new app (script type)',
                    '3. Copy client ID and client secret',
                    '4. Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env'
                ],
                'env_vars': ['REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET', 'REDDIT_USER_AGENT']
            },
            'youtube': {
                'description': 'YouTube Data API for video comments analysis',
                'steps': [
                    '1. Go to Google Cloud Console',
                    '2. Enable YouTube Data API v3',
                    '3. Create API credentials',
                    '4. Set YOUTUBE_API_KEY in .env'
                ],
                'env_vars': ['YOUTUBE_API_KEY']
            },
            'instagram': {
                'description': 'Instagram Graph API for social media data',
                'steps': [
                    '1. Create Facebook Developer Account',
                    '2. Create Instagram Basic Display App',
                    '3. Get access token for your Instagram Business Account',
                    '4. Set INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_USER_ID in .env'
                ],
                'env_vars': ['INSTAGRAM_ACCESS_TOKEN', 'INSTAGRAM_USER_ID', 'INSTAGRAM_APP_ID', 'INSTAGRAM_APP_SECRET']
            },
            'claude': {
                'description': 'Claude API for advanced sentiment analysis and web search',
                'steps': [
                    '1. Go to https://console.anthropic.com',
                    '2. Create account and get API key',
                    '3. Set CLAUDE_API_KEY in .env',
                    '4. This enables both sentiment analysis and web search capabilities'
                ],
                'env_vars': ['CLAUDE_API_KEY']
            },
            'perplexity': {
                'description': 'Perplexity AI for real-time market analysis',
                'steps': [
                    '1. Go to https://perplexity.ai',
                    '2. Get API access (Pro subscription required)',
                    '3. Set PERPLEXITY_API_KEY in .env'
                ],
                'env_vars': ['PERPLEXITY_API_KEY']
            }
        }
             
        
        return {component: guides[component] for component in missing if component in guides}