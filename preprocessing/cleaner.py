import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
import string
import logging
from typing import List

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

logger = logging.getLogger(__name__)

class TextCleaner:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.stemmer = PorterStemmer()
    
    def clean_text(self, text: str) -> str:
        """Clean and preprocess text data"""
        if not text:
            return ""
        
        try:
            # Convert to lowercase
            text = text.lower()
            
            # Remove URLs
            text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
            
            # Remove email addresses
            text = re.sub(r'\S+@\S+', '', text)
            
            # Remove mentions and hashtags (but keep the text)
            text = re.sub(r'[@#]\w+', '', text)
            
            # Remove special characters and digits
            text = re.sub(r'[^a-zA-Z\s]', '', text)
            
            # Remove extra whitespace
            text = ' '.join(text.split())
            
            # Tokenize
            tokens = word_tokenize(text)
            
            # Remove stopwords and short words
            tokens = [token for token in tokens if token not in self.stop_words and len(token) > 2]
            
            # Stem words
            tokens = [self.stemmer.stem(token) for token in tokens]
            
            return ' '.join(tokens)
            
        except Exception as e:
            logger.error(f"Error cleaning text: {e}")
            return text
    
    def extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        """Extract key terms from text"""
        try:
            from keybert import KeyBERT
            kw_model = KeyBERT()
            keywords = kw_model.extract_keywords(text, keyphrase_ngram_range=(1, 2), 
                                               stop_words='english', top_k=top_k)
            return [kw[0] for kw in keywords]
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []