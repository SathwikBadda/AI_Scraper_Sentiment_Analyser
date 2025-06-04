import os
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from pathlib import Path
import json
import logging
from cryptography.fernet import Fernet
import base64

logger = logging.getLogger(__name__)

@dataclass
class APICredentials:
    """Data class for API credentials"""
    api_key: str
    secret: Optional[str] = None
    token: Optional[str] = None
    additional_params: Optional[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.additional_params is None:
            self.additional_params = {}

class APIKeyManager:
    """Secure API key management system"""
    
    def __init__(self, config_file: str = ".env", encrypted_file: str = "config/keys.enc"):
        self.config_file = Path(config_file)
        self.encrypted_file = Path(encrypted_file)
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        self._api_keys: Dict[str, APICredentials] = {}
        self._load_keys()
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for secure storage"""
        key_file = Path("config/.key")
        
        if key_file.exists():
            try:
                with open(key_file, 'rb') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Could not read encryption key: {e}")
        
        # Create new key
        key = Fernet.generate_key()
        try:
            key_file.parent.mkdir(exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            logger.info("Created new encryption key")
        except Exception as e:
            logger.warning(f"Could not save encryption key: {e}")
        
        return key
    
    def _load_keys(self):
        """Load API keys from various sources"""
        # Load from .env file
        self._load_from_env()
        
        # Load from encrypted file
        self._load_from_encrypted_file()
        
        # Load from environment variables
        self._load_from_environment()
    
    def _load_from_env(self):
        """Load keys from .env file"""
        if not self.config_file.exists():
            logger.warning(f"Config file not found: {self.config_file}")
            return
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    
                    try:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        
                        if self._is_api_key(key):
                            api_name = self._extract_api_name(key)
                            self._store_api_key(api_name, key, value)
                            
                    except ValueError:
                        logger.warning(f"Invalid line {line_num} in {self.config_file}: {line}")
            
            logger.info(f"Loaded API keys from {self.config_file}")
            
        except Exception as e:
            logger.error(f"Error loading from .env file: {e}")
    
    def _load_from_encrypted_file(self):
        """Load keys from encrypted file"""
        if not self.encrypted_file.exists():
            return
        
        try:
            with open(self.encrypted_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            keys_data = json.loads(decrypted_data.decode('utf-8'))
            
            for api_name, credentials in keys_data.items():
                self._api_keys[api_name] = APICredentials(**credentials)
            
            logger.info("Loaded API keys from encrypted file")
            
        except Exception as e:
            logger.error(f"Error loading from encrypted file: {e}")
    
    def _load_from_environment(self):
        """Load keys from environment variables"""
        env_mappings = {
            'YOUTUBE_API_KEY': ('youtube', 'api_key'),
            'REDDIT_CLIENT_ID': ('reddit', 'api_key'),
            'REDDIT_CLIENT_SECRET': ('reddit', 'secret'),
            'REDDIT_USER_AGENT': ('reddit', 'user_agent'),
            'TWITTER_BEARER_TOKEN': ('twitter', 'token'),
            'TWITTER_API_KEY': ('twitter', 'api_key'),
            'TWITTER_API_SECRET': ('twitter', 'secret'),
            'PERPLEXITY_API_KEY': ('perplexity', 'api_key'),
            'OPENAI_API_KEY': ('openai', 'api_key'),
            'HUGGINGFACE_API_KEY': ('huggingface', 'api_key'),
        }
        
        for env_var, (api_name, key_type) in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                if api_name not in self._api_keys:
                    self._api_keys[api_name] = APICredentials(api_key="")
                
                if key_type == 'api_key':
                    self._api_keys[api_name].api_key = value
                elif key_type == 'secret':
                    self._api_keys[api_name].secret = value
                elif key_type == 'token':
                    self._api_keys[api_name].token = value
                else:
                    if not self._api_keys[api_name].additional_params:
                        self._api_keys[api_name].additional_params = {}
                    self._api_keys[api_name].additional_params[key_type] = value
    
    def _is_api_key(self, key_name: str) -> bool:
        """Check if key name represents an API key"""
        api_indicators = [
            'api_key', 'client_id', 'client_secret', 'bearer_token',
            'access_token', 'secret_key', 'private_key', 'user_agent'
        ]
        key_lower = key_name.lower()
        return any(indicator in key_lower for indicator in api_indicators)
    
    def _extract_api_name(self, key_name: str) -> str:
        """Extract API service name from key name"""
        key_lower = key_name.lower()
        
        api_names = {
            'youtube': 'youtube',
            'reddit': 'reddit',
            'twitter': 'twitter',
            'perplexity': 'perplexity',
            'openai': 'openai',
            'huggingface': 'huggingface',
            'instagram': 'instagram',
            'facebook': 'facebook',
            'google': 'google'
        }
        
        for api_identifier, api_name in api_names.items():
            if api_identifier in key_lower:
                return api_name
        
        # Extract from pattern like "SERVICE_API_KEY"
        parts = key_lower.split('_')
        if len(parts) > 1:
            return parts[0]
        
        return 'unknown'
    
    def _store_api_key(self, api_name: str, key_type: str, value: str):
        """Store API key in internal structure"""
        if api_name not in self._api_keys:
            self._api_keys[api_name] = APICredentials(api_key="")
        
        key_type_lower = key_type.lower()
        
        if 'api_key' in key_type_lower or 'client_id' in key_type_lower:
            self._api_keys[api_name].api_key = value
        elif 'secret' in key_type_lower:
            self._api_keys[api_name].secret = value
        elif 'token' in key_type_lower:
            self._api_keys[api_name].token = value
        else:
            if not self._api_keys[api_name].additional_params:
                self._api_keys[api_name].additional_params = {}
            param_name = key_type_lower.replace(f"{api_name.lower()}_", "")
            self._api_keys[api_name].additional_params[param_name] = value
    
    def get_api_key(self, api_name: str) -> Optional[str]:
        """Get API key for specific service"""
        credentials = self._api_keys.get(api_name.lower())
        return credentials.api_key if credentials else None
    
    def get_credentials(self, api_name: str) -> Optional[APICredentials]:
        """Get complete credentials for specific service"""
        return self._api_keys.get(api_name.lower())
    
    def validate_api_key(self, api_name: str) -> Tuple[bool, str]:
        """Validate API key for specific service"""
        credentials = self.get_credentials(api_name)
        
        if not credentials:
            return False, f"No credentials found for {api_name}"
        
        if not credentials.api_key:
            return False, f"No API key found for {api_name}"
        
        # Basic validation
        api_key = credentials.api_key.strip()
        
        if len(api_key) < 10:
            return False, f"API key too short for {api_name}"
        
        # Check for placeholder values
        invalid_values = [
            'your_api_key', 'api_key_here', 'replace_with_your_key', 
            'none', 'null', 'undefined', 'todo', 'changeme'
        ]
        
        if api_key.lower() in invalid_values:
            return False, f"Placeholder API key detected for {api_name}"
        
        # Service-specific validations
        validation_rules = {
            'youtube': lambda k: k.startswith('AIza') and len(k) == 39,
            'reddit': lambda k: len(k) >= 14,
            'twitter': lambda k: len(k) >= 20,
            'perplexity': lambda k: len(k) >= 32,
            'openai': lambda k: k.startswith('sk-') and len(k) >= 40,
        }
        
        if api_name in validation_rules:
            if not validation_rules[api_name](api_key):
                return False, f"Invalid format for {api_name} API key"
        
        return True, f"Valid API key for {api_name}"
    
    def get_all_api_status(self) -> Dict[str, Dict[str, any]]:
        """Get validation status for all APIs"""
        status = {}
        
        expected_apis = ['youtube', 'reddit', 'twitter', 'perplexity', 'openai']
        
        for api_name in expected_apis:
            is_valid, message = self.validate_api_key(api_name)
            credentials = self.get_credentials(api_name)
            
            status[api_name] = {
                'configured': credentials is not None,
                'valid': is_valid,
                'message': message,
                'has_secret': credentials.secret is not None if credentials else False,
                'has_token': credentials.token is not None if credentials else False,
                'additional_params': list(credentials.additional_params.keys()) if credentials and credentials.additional_params else []
            }
        
        return status
    
    def save_encrypted_keys(self):
        """Save API keys to encrypted file"""
        try:
            # Convert to serializable format
            data_to_encrypt = {}
            for api_name, credentials in self._api_keys.items():
                data_to_encrypt[api_name] = {
                    'api_key': credentials.api_key,
                    'secret': credentials.secret,
                    'token': credentials.token,
                    'additional_params': credentials.additional_params
                }
            
            # Encrypt and save
            json_data = json.dumps(data_to_encrypt)
            encrypted_data = self.cipher.encrypt(json_data.encode('utf-8'))
            
            self.encrypted_file.parent.mkdir(exist_ok=True)
            with open(self.encrypted_file, 'wb') as f:
                f.write(encrypted_data)
            
            logger.info("API keys saved to encrypted file")
            
        except Exception as e:
            logger.error(f"Error saving encrypted keys: {e}")
    
    def add_api_key(self, api_name: str, api_key: str, secret: str = None, 
                   token: str = None, additional_params: Dict[str, str] = None):
        """Add or update API key"""
        self._api_keys[api_name.lower()] = APICredentials(
            api_key=api_key,
            secret=secret,
            token=token,
            additional_params=additional_params or {}
        )
        
        logger.info(f"Added/updated API key for {api_name}")
    
    def remove_api_key(self, api_name: str):
        """Remove API key"""
        if api_name.lower() in self._api_keys:
            del self._api_keys[api_name.lower()]
            logger.info(f"Removed API key for {api_name}")
    
    def list_configured_apis(self) -> List[str]:
        """List all configured APIs"""
        return list(self._api_keys.keys())
    
    def export_template(self, file_path: str = ".env.template"):
        """Export template file with API key placeholders"""
        template_content = """# Real Estate Sentiment Analysis - API Configuration
# Copy this file to .env and fill in your actual API keys

# YouTube Data API v3 (Google Cloud Console)
YOUTUBE_API_KEY=your_youtube_api_key_here

# Reddit API (https://www.reddit.com/prefs/apps)
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
REDDIT_USER_AGENT=RealEstateSentiment/1.0

# Twitter API (Optional - snscrape used as fallback)
TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here
TWITTER_API_KEY=your_twitter_api_key_here
TWITTER_API_SECRET=your_twitter_api_secret_here

# Perplexity AI API
PERPLEXITY_API_KEY=your_perplexity_api_key_here

# OpenAI API (Optional - for advanced NLP)
OPENAI_API_KEY=your_openai_api_key_here

# Hugging Face API (Optional - for transformer models)
HUGGINGFACE_API_KEY=your_huggingface_api_key_here

# Database Configuration
DATABASE_URL=sqlite:///real_estate_sentiment.db

# Application Settings
DEBUG=False
LOG_LEVEL=INFO
"""
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(template_content)
            logger.info(f"Template exported to {file_path}")
        except Exception as e:
            logger.error(f"Error exporting template: {e}")

# Global instance
_api_manager = None

def get_api_manager() -> APIKeyManager:
    """Get global API manager instance"""
    global _api_manager
    if _api_manager is None:
        _api_manager = APIKeyManager()
    return _api_manager

def get_api_key(api_name: str) -> Optional[str]:
    """Quick access to API key"""
    return get_api_manager().get_api_key(api_name)

def get_credentials(api_name: str) -> Optional[APICredentials]:
    """Quick access to credentials"""
    return get_api_manager().get_credentials(api_name)

def validate_all_apis() -> Dict[str, Dict[str, any]]:
    """Validate all configured APIs"""
    return get_api_manager().get_all_api_status()

# Configuration validation for specific services
class APIValidator:
    """Service-specific API validation"""
    
    @staticmethod
    def validate_youtube_api(api_key: str) -> Tuple[bool, str]:
        """Validate YouTube API key"""
        try:
            from googleapiclient.discovery import build
            youtube = build('youtube', 'v3', developerKey=api_key)
            
            # Test with a simple request
            request = youtube.search().list(
                part='snippet',
                q='test',
                maxResults=1
            )
            request.execute()
            
            return True, "YouTube API key is valid"
            
        except Exception as e:
            return False, f"YouTube API validation failed: {str(e)}"
    
    @staticmethod
    def validate_reddit_api(client_id: str, client_secret: str, user_agent: str) -> Tuple[bool, str]:
        """Validate Reddit API credentials"""
        try:
            import praw
            reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            
            # Test with a simple request
            reddit.subreddit('test').hot(limit=1)
            
            return True, "Reddit API credentials are valid"
            
        except Exception as e:
            return False, f"Reddit API validation failed: {str(e)}"
    
    @staticmethod
    def validate_perplexity_api(api_key: str) -> Tuple[bool, str]:
        """Validate Perplexity API key"""
        try:
            import requests
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1
            }
            
            response = requests.post(
                "https://api.perplexity.ai/chat/completions",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return True, "Perplexity API key is valid"
            else:
                return False, f"Perplexity API validation failed: HTTP {response.status_code}"
                
        except Exception as e:
            return False, f"Perplexity API validation failed: {str(e)}"

# CLI for API key management
def main():
    """CLI interface for API key management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="API Key Management for Real Estate Sentiment Analysis")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List configured APIs')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Check API status')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate API keys')
    validate_parser.add_argument('--api', help='Specific API to validate')
    
    # Template command
    template_parser = subparsers.add_parser('template', help='Export configuration template')
    template_parser.add_argument('--output', default='.env.template', help='Output file path')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add API key')
    add_parser.add_argument('api_name', help='API service name')
    add_parser.add_argument('api_key', help='API key value')
    add_parser.add_argument('--secret', help='API secret (if required)')
    add_parser.add_argument('--token', help='API token (if required)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = get_api_manager()
    
    if args.command == 'list':
        apis = manager.list_configured_apis()
        print("Configured APIs:")
        for api in apis:
            print(f"  - {api}")
    
    elif args.command == 'status':
        status = manager.get_all_api_status()
        print("API Status:")
        for api_name, info in status.items():
            status_icon = "✅" if info['valid'] else "❌" if info['configured'] else "⚪"
            print(f"  {status_icon} {api_name}: {info['message']}")
    
    elif args.command == 'validate':
        if args.api:
            is_valid, message = manager.validate_api_key(args.api)
            print(f"{args.api}: {'✅' if is_valid else '❌'} {message}")
        else:
            status = manager.get_all_api_status()
            for api_name, info in status.items():
                status_icon = "✅" if info['valid'] else "❌"
                print(f"{status_icon} {api_name}: {info['message']}")
    
    elif args.command == 'template':
        manager.export_template(args.output)
        print(f"Template exported to {args.output}")
    
    elif args.command == 'add':
        manager.add_api_key(args.api_name, args.api_key, args.secret, args.token)
        manager.save_encrypted_keys()
        print(f"Added API key for {args.api_name}")

if __name__ == "__main__":
    main()