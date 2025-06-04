import re
from config.config import Config
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class LocationExtractor:
    def __init__(self):
        self.hyderabad_localities = Config.HYDERABAD_LOCALITIES
        # Create regex pattern for all localities
        self.locality_pattern = '|'.join([re.escape(loc) for loc in self.hyderabad_localities])
    
    def extract_location(self, text: str) -> Optional[str]:
        """Extract Hyderabad locality from text"""
        if not text:
            return None
        
        try:
            # Convert to lowercase for matching
            text_lower = text.lower()
            
            # Check for each locality
            for locality in self.hyderabad_localities:
                if locality.lower() in text_lower:
                    return locality
            
            # Check for common misspellings or variations
            locality_variations = {
                'kondapur': 'kondapur',
                'gachi': 'gachibowli',
                'gachibowli': 'gachibowli',
                'madhapur': 'madhapur',
                'hitech': 'hitech city',
                'hitec': 'hitech city',
                'banjara': 'banjara hills',
                'jubilee': 'jubilee hills',
                'kukatpally': 'kukatpally',
                'miyapur': 'miyapur',
                'secunderabad': 'secunderabad',
                'ameerpet': 'ameerpet',
                'dilsukhnagar': 'dilsukhnagar',
                'uppal': 'uppal',
                'kompally': 'kompally',
                'manikonda': 'manikonda',
                'kokapet': 'kokapet',
                'financial district': 'financial district',
                'nanakramguda': 'financial district',
                'gachibowli': 'gachibowli'
            }
            
            for variant, standard_name in locality_variations.items():
                if variant in text_lower:
                    return standard_name
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting location: {e}")
            return None
    
    def is_hyderabad_related(self, text: str) -> bool:
        """Check if text is related to Hyderabad"""
        if not text:
            return False
        
        text_lower = text.lower()
        hyderabad_indicators = [
            'hyderabad', 'hyd', 'telangana', 'cyberabad', 'secunderabad',
            'charminar', 'hitec city', 'gachibowli', 'jubilee hills'
        ]
        
        return any(indicator in text_lower for indicator in hyderabad_indicators)