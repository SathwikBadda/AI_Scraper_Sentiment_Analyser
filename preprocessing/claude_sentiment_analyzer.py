# preprocessing/claude_sentiment_analyzer.py
import anthropic
import requests
import json
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
from config.config import Config
import re
import time

logger = logging.getLogger(__name__)

class EnhancedSentimentAnalyzer:
    def __init__(self):
        self.claude_client = None
        self.api_key = Config.CLAUDE_API_KEY
        
        if self.api_key:
            try:
                self.claude_client = anthropic.Anthropic(api_key=self.api_key)
                logger.info("✅ Claude client initialized successfully")
            except Exception as e:
                logger.error(f"❌ Error initializing Claude client: {e}")
        
        # Cache for search results and sentiment analysis to avoid repeated API calls
        self.search_cache = {}
        self.sentiment_cache = {}
        
    def is_configured(self) -> bool:
        """Check if Claude API is properly configured with connection test"""
        if not self.claude_client:
            return False
        
        # Test API connection
        try:
            test_response = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=50,
                messages=[{
                    "role": "user",
                    "content": "Test. Reply: READY"
                }]
            )
            
            response_text = test_response.content[0].text.strip().upper()
            is_working = "READY" in response_text
            
            if is_working:
                logger.info("✅ Claude sentiment analyzer ready")
            else:
                logger.warning("⚠️ Claude API responding but may have issues")
            
            return is_working
            
        except Exception as e:
            logger.error(f"❌ Claude API test failed: {e}")
            return False
    
    def web_search(self, query: str, location: str, num_results: int = 10) -> List[Dict]:
        """Perform web search using Claude's built-in search capabilities"""
        search_results = []
        
        try:
            # Create cache key
            cache_key = f"{query}_{location}_{num_results}"
            if cache_key in self.search_cache:
                return self.search_cache[cache_key]
            
            if not self.claude_client:
                logger.warning("Claude API not available for web search")
                return []
            
            # Construct search query for Claude
            search_prompt = f"""
Please search for current information about {query} in {location} real estate market. I need the latest market data, trends, prices, and sentiment information.

Provide me with:
1. Current property prices and recent trends in {location}
2. Market sentiment and investor confidence
3. Recent news and developments affecting {location} real estate
4. Expert opinions and analyst reports
5. Demand and supply dynamics
6. Infrastructure developments impacting property values

Please search the web and provide specific, recent information with sources where possible. Focus on data from the last 6 months.
"""
            
            response = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",  # Updated to current model
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": search_prompt
                }]
            )
            
            # Parse Claude's response to extract search information
            search_content = response.content[0].text
            
            # Create structured search results from Claude's response
            search_results = [{
                'title': f"Real Estate Market Analysis for {location}",
                'description': search_content[:500] + "...",
                'content': search_content,
                'url': 'https://claude.ai/search',
                'source': 'claude_web_search',
                'timestamp': datetime.now().isoformat()
            }]
            
            # Try to extract specific data points and create additional structured results
            if "price" in search_content.lower() or "₹" in search_content:
                price_info = self._extract_price_information(search_content, location)
                if price_info:
                    search_results.append(price_info)
            
            if "sentiment" in search_content.lower() or "opinion" in search_content.lower():
                sentiment_info = self._extract_sentiment_information(search_content, location)
                if sentiment_info:
                    search_results.append(sentiment_info)
            
            if "news" in search_content.lower() or "development" in search_content.lower():
                news_info = self._extract_news_information(search_content, location)
                if news_info:
                    search_results.append(news_info)
            
            # Cache the results
            self.search_cache[cache_key] = search_results
        
        except Exception as e:
            logger.error(f"Error performing Claude web search: {e}")
        
        logger.info(f"Found {len(search_results)} Claude search results for: {query} in {location}")
        return search_results
    
    def _extract_price_information(self, content: str, location: str) -> Dict:
        """Extract price information from Claude's search response"""
        try:
            price_prompt = f"""
From the following content about {location} real estate, extract specific price information and trends:

{content[:1000]}

Please provide a structured summary focusing on:
1. Current average property prices
2. Price trends (rising/falling/stable)
3. Price ranges for different property types
4. Year-over-year price changes

Format as a brief, factual summary.
"""
            
            response = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",  # Updated to current model
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": price_prompt
                }]
            )
            
            return {
                'title': f"Property Price Analysis - {location}",
                'description': response.content[0].text[:200] + "...",
                'content': response.content[0].text,
                'url': 'https://claude.ai/analysis',
                'source': 'claude_price_analysis',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error extracting price information: {e}")
            return None
    
    def _extract_sentiment_information(self, content: str, location: str) -> Dict:
        """Extract sentiment information from Claude's search response"""
        try:
            sentiment_prompt = f"""
From the following content about {location} real estate, extract market sentiment and opinion information:

{content[:1000]}

Please provide a structured summary focusing on:
1. Overall market sentiment (positive/negative/neutral)
2. Investor confidence levels
3. Expert opinions and recommendations
4. Market mood and outlook

Format as a brief, factual summary.
"""
            
            response = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",  # Updated to current model
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": sentiment_prompt
                }]
            )
            
            return {
                'title': f"Market Sentiment Analysis - {location}",
                'description': response.content[0].text[:200] + "...",
                'content': response.content[0].text,
                'url': 'https://claude.ai/analysis',
                'source': 'claude_sentiment_analysis',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error extracting sentiment information: {e}")
            return None
    
    def _extract_news_information(self, content: str, location: str) -> Dict:
        """Extract news and developments from Claude's search response"""
        try:
            news_prompt = f"""
From the following content about {location} real estate, extract recent news and developments:

{content[:1000]}

Please provide a structured summary focusing on:
1. Recent developments and project launches
2. Infrastructure improvements
3. Policy changes affecting real estate
4. Market disruptions or opportunities

Format as a brief, factual summary.
"""
            
            response = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",  # Updated to current model
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": news_prompt
                }]
            )
            
            return {
                'title': f"Recent Developments - {location}",
                'description': response.content[0].text[:200] + "...",
                'content': response.content[0].text,
                'url': 'https://claude.ai/analysis',
                'source': 'claude_news_analysis',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error extracting news information: {e}")
            return None
    
    def _duckduckgo_search(self, query: str, num_results: int = 10) -> List[Dict]:
        """Fallback search using Claude with specific search instructions"""
        search_results = []
        
        try:
            if not self.claude_client:
                return []
            
            search_prompt = f"""
Please provide current information about: {query}

Search for and provide:
1. Recent news articles and reports
2. Current market data and statistics
3. Expert analysis and opinions
4. Property listings and price information
5. Market trends and forecasts

Provide specific, factual information with as much detail as possible about the current market situation.
"""
            
            response = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",  # Updated to current model
                max_tokens=1500,
                messages=[{
                    "role": "user",
                    "content": search_prompt
                }]
            )
            
            # Split response into multiple search result entries
            content = response.content[0].text
            
            # Try to identify different sections and create separate results
            sections = content.split('\n\n')
            
            for i, section in enumerate(sections[:num_results]):
                if len(section.strip()) > 50:  # Only include substantial sections
                    search_results.append({
                        'title': f"Market Analysis {i+1}",
                        'description': section[:200] + "...",
                        'content': section,
                        'url': 'https://claude.ai/search',
                        'source': 'claude_general_search',
                        'timestamp': datetime.now().isoformat()
                    })
        
        except Exception as e:
            logger.error(f"Error with Claude fallback search: {e}")
        
        return search_results
    
    def analyze_market_context(self, location: str) -> Dict:
        """Get current market context for the location using Claude's search capabilities"""
        try:
            if not self.claude_client:
                return self._get_fallback_market_context()
            
            # Use Claude to search for and analyze current market trends
            market_analysis_prompt = f"""
Please provide a comprehensive analysis of the current real estate market in {location}, Hyderabad. 

Search for and analyze:
1. Current market trends and price movements
2. Recent property transactions and price data
3. Market sentiment from recent news and reports
4. Infrastructure developments affecting the area
5. Investment outlook and expert opinions
6. Demand and supply dynamics
7. Comparison with other areas in Hyderabad

Based on your search and analysis, provide a JSON response with the following structure:
{{
    "market_sentiment": "Positive/Negative/Neutral",
    "key_trends": ["trend1", "trend2", "trend3"],
    "price_direction": "Rising/Falling/Stable",
    "market_activity": "High/Medium/Low",
    "context_summary": "Brief summary of current market conditions",
    "price_range": "Current price range information",
    "investment_outlook": "Short-term investment outlook",
    "risk_factors": ["risk1", "risk2"],
    "growth_drivers": ["driver1", "driver2"]
}}

Focus on the most recent information available and provide specific insights about {location}.
"""
            
            response = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",  # Updated to current model
                max_tokens=1500,
                messages=[{
                    "role": "user",
                    "content": market_analysis_prompt
                }]
            )
            
            # Try to parse JSON response
            try:
                # Extract JSON from response if it exists
                response_text = response.content[0].text
                
                # Look for JSON structure in the response
                import re
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
                
                if json_match:
                    analysis = json.loads(json_match.group())
                    return analysis
                else:
                    # If no JSON found, create structured response from text
                    return self._parse_market_analysis_text(response_text, location)
            
            except json.JSONDecodeError:
                # Fallback: parse the text response and create structured data
                return self._parse_market_analysis_text(response.content[0].text, location)
        
        except Exception as e:
            logger.error(f"Error analyzing market context with Claude: {e}")
            return self._get_fallback_market_context()
    
    def _parse_market_analysis_text(self, text: str, location: str) -> Dict:
        """Parse Claude's text response into structured market analysis"""
        try:
            # Extract sentiment from text
            text_lower = text.lower()
            
            if any(word in text_lower for word in ['positive', 'bullish', 'growing', 'strong', 'rising']):
                market_sentiment = 'Positive'
                price_direction = 'Rising'
            elif any(word in text_lower for word in ['negative', 'bearish', 'declining', 'weak', 'falling']):
                market_sentiment = 'Negative'
                price_direction = 'Falling'
            else:
                market_sentiment = 'Neutral'
                price_direction = 'Stable'
            
            # Extract activity level
            if any(word in text_lower for word in ['high activity', 'active', 'busy', 'strong demand']):
                market_activity = 'High'
            elif any(word in text_lower for word in ['low activity', 'slow', 'weak demand']):
                market_activity = 'Low'
            else:
                market_activity = 'Medium'
            
            # Extract key trends from the text
            sentences = text.split('.')
            key_trends = []
            growth_drivers = []
            risk_factors = []
            
            for sentence in sentences[:10]:  # Limit to first 10 sentences
                sentence = sentence.strip()
                if len(sentence) > 20:
                    if any(word in sentence.lower() for word in ['trend', 'increasing', 'growing', 'development']):
                        key_trends.append(sentence[:100])
                    elif any(word in sentence.lower() for word in ['infrastructure', 'metro', 'connectivity', 'growth']):
                        growth_drivers.append(sentence[:100])
                    elif any(word in sentence.lower() for word in ['risk', 'challenge', 'concern', 'issue']):
                        risk_factors.append(sentence[:100])
            
            return {
                'market_sentiment': market_sentiment,
                'key_trends': key_trends[:3] or [f"Market analysis for {location} completed"],
                'price_direction': price_direction,
                'market_activity': market_activity,
                'context_summary': text[:300] + "..." if len(text) > 300 else text,
                'price_range': 'Analysis based on current market data',
                'investment_outlook': market_sentiment,
                'risk_factors': risk_factors[:2] or ['Standard market risks apply'],
                'growth_drivers': growth_drivers[:2] or ['Location-specific factors']
            }
        
        except Exception as e:
            logger.error(f"Error parsing market analysis text: {e}")
            return self._get_fallback_market_context()
    
    def _get_fallback_market_context(self) -> Dict:
        """Provide fallback market context when Claude is not available"""
        return {
            'market_sentiment': 'Neutral',
            'key_trends': ['Real estate market analysis'],
            'price_direction': 'Stable',
            'market_activity': 'Medium',
            'context_summary': 'Market analysis unavailable - using basic assessment',
            'price_range': 'Price data requires market research',
            'investment_outlook': 'Neutral',
            'risk_factors': ['Market volatility', 'Economic factors'],
            'growth_drivers': ['Infrastructure development', 'Location advantages']
        }
    
    def analyze_sentiment_batch(self, texts: List[str], location: str) -> List[Dict]:
        """Analyze sentiment for multiple texts with market context"""
        if not texts:
            return []
        
        if not self.is_configured():
            logger.warning("Claude API not configured, using fallback sentiment analysis")
            return self._fallback_sentiment_analysis(texts)
        
        try:
            # Get market context once for the batch
            market_context = self.analyze_market_context(location)
            
            # Process in batches to respect API limits
            batch_size = 10
            all_results = []
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_results = self._analyze_batch_with_claude(batch_texts, location, market_context)
                all_results.extend(batch_results)
                
                # Rate limiting
                if i + batch_size < len(texts):
                    time.sleep(1)  # Prevent rate limiting
            
            return all_results
        
        except Exception as e:
            logger.error(f"Error in batch sentiment analysis: {e}")
            return self._fallback_sentiment_analysis(texts)
    
    def _analyze_batch_with_claude(self, texts: List[str], location: str, market_context: Dict) -> List[Dict]:
        """Analyze a batch of texts using Claude with market context"""
        results = []
        
        try:
            # Prepare batch analysis prompt
            batch_prompt = f"""
You are an expert real estate sentiment analyst. Analyze the sentiment of the following social media posts/comments about real estate in {location}.

Current Market Context for {location}:
- Market Sentiment: {market_context['market_sentiment']}
- Price Direction: {market_context['price_direction']}
- Market Activity: {market_context['market_activity']}
- Key Trends: {', '.join(market_context['key_trends'])}
- Summary: {market_context['context_summary']}

For each text, provide sentiment analysis considering:
1. Overall emotional tone (positive, negative, neutral)
2. Real estate specific sentiment (bullish, bearish, neutral)
3. Price sentiment (optimistic, pessimistic, neutral)
4. Investment sentiment (confident, cautious, neutral)
5. Market context alignment

Texts to analyze:
"""
            
            for i, text in enumerate(texts):
                batch_prompt += f"\n{i+1}. {text[:500]}..."  # Limit text length
            
            batch_prompt += """

Please provide a JSON array with analysis for each text:
[
    {
        "text_index": 1,
        "overall_sentiment": "Positive/Negative/Neutral",
        "sentiment_score": 0.0,  // -1.0 to 1.0
        "confidence": 0.0,  // 0.0 to 1.0
        "real_estate_sentiment": "Bullish/Bearish/Neutral",
        "price_sentiment": "Optimistic/Pessimistic/Neutral", 
        "investment_sentiment": "Confident/Cautious/Neutral",
        "key_factors": ["factor1", "factor2"],
        "reason": "Brief explanation of the sentiment analysis"
    }
]
"""
            
            response = self.claude_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": batch_prompt
                }]
            )
            
            # Parse JSON response
            try:
                analysis_results = json.loads(response.content[0].text)
                
                for i, analysis in enumerate(analysis_results):
                    if i < len(texts):
                        results.append({
                            'sentiment': analysis.get('overall_sentiment', 'Neutral'),
                            'score': float(analysis.get('sentiment_score', 0.0)),
                            'confidence': float(analysis.get('confidence', 0.5)),
                            'real_estate_sentiment': analysis.get('real_estate_sentiment', 'Neutral'),
                            'price_sentiment': analysis.get('price_sentiment', 'Neutral'),
                            'investment_sentiment': analysis.get('investment_sentiment', 'Neutral'),
                            'key_factors': analysis.get('key_factors', []),
                            'reason': analysis.get('reason', 'Analyzed with Claude'),
                            'analysis_type': 'comprehensive',
                            'market_context': market_context
                        })
            
            except json.JSONDecodeError:
                # Fallback to individual analysis
                for text in texts:
                    result = self.analyze_sentiment(text, location)
                    results.append(result)
        
        except Exception as e:
            logger.error(f"Error in Claude batch analysis: {e}")
            # Fallback
            for text in texts:
                results.append(self._fallback_single_analysis(text))
        
        return results
    
    def analyze_sentiment(self, text: str, location: str = None) -> Dict:
        """Analyze sentiment of a single text with enhanced Claude analysis"""
        if not text or not text.strip():
            return {
                'sentiment': 'Neutral',
                'score': 0.0,
                'confidence': 0.0,
                'reason': 'Empty text',
                'analysis_type': 'empty'
            }
        
        # Check cache
        cache_key = f"{text[:100]}_{location}"
        if cache_key in self.sentiment_cache:
            return self.sentiment_cache[cache_key]
        
        if not self.is_configured():
            return self._fallback_single_analysis(text)
        
        try:
            # Get current market context if location provided
            market_context = {}
            if location:
                market_context = self.analyze_market_context(location)
            
            prompt = f"""
Analyze the sentiment of this real estate-related text with enhanced context:

Text: "{text}"
Location: {location or 'Not specified'}

Current Market Context:
{json.dumps(market_context, indent=2) if market_context else 'No market context available'}

Provide comprehensive sentiment analysis considering:
1. Overall emotional tone
2. Real estate market sentiment
3. Price/value sentiment  
4. Investment confidence
5. Market timing sentiment
6. Risk perception

Respond in JSON format:
{{
    "sentiment": "Positive/Negative/Neutral",
    "score": 0.0,  // -1.0 (very negative) to 1.0 (very positive)
    "confidence": 0.0,  // 0.0 to 1.0
    "real_estate_sentiment": "Bullish/Bearish/Neutral",
    "price_sentiment": "Optimistic/Pessimistic/Neutral",
    "investment_sentiment": "Confident/Cautious/Neutral",
    "market_timing": "Good/Poor/Neutral",
    "risk_perception": "Low/Medium/High",
    "key_indicators": ["indicator1", "indicator2"],
    "reason": "Detailed explanation of sentiment analysis",
    "analysis_type": "comprehensive"
}}
"""
            
            response = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",  # Updated to current model
                max_tokens=1000,
                messages=[{
                    "role": "user", 
                    "content": prompt
                }]
            )
            
            # Parse response
            try:
                result = json.loads(response.content[0].text)
                
                # Add market context to result
                if market_context:
                    result['market_context'] = market_context
                
                # Cache the result
                self.sentiment_cache[cache_key] = result
                return result
            
            except json.JSONDecodeError:
                # Extract sentiment from text response
                response_text = response.content[0].text.lower()
                
                if 'positive' in response_text:
                    sentiment = 'Positive'
                    score = 0.6
                elif 'negative' in response_text:
                    sentiment = 'Negative'
                    score = -0.6
                else:
                    sentiment = 'Neutral'
                    score = 0.0
                
                return {
                    'sentiment': sentiment,
                    'score': score,
                    'confidence': 0.7,
                    'reason': response.content[0].text[:200],
                    'analysis_type': 'text_parsed'
                }
        
        except Exception as e:
            logger.error(f"Error analyzing sentiment with Claude: {e}")
            return self._fallback_single_analysis(text)
    
    def _fallback_sentiment_analysis(self, texts: List[str]) -> List[Dict]:
        """Fallback sentiment analysis using simple keyword matching"""
        results = []
        
        positive_keywords = [
            'good', 'great', 'excellent', 'amazing', 'fantastic', 'wonderful',
            'buy', 'invest', 'opportunity', 'profitable', 'growth', 'rising',
            'affordable', 'value', 'deal', 'recommended', 'bullish', 'optimistic'
        ]
        
        negative_keywords = [
            'bad', 'terrible', 'awful', 'horrible', 'disappointing', 'overpriced',
            'expensive', 'risky', 'avoid', 'falling', 'crash', 'bubble',
            'bearish', 'pessimistic', 'declining', 'loss', 'fraud', 'scam'
        ]
        
        for text in texts:
            results.append(self._fallback_single_analysis(text))
        
        return results
    
    def _fallback_single_analysis(self, text: str) -> Dict:
        """Fallback analysis for single text"""
        text_lower = text.lower()
        
        positive_keywords = [
            'good', 'great', 'excellent', 'amazing', 'fantastic', 'wonderful',
            'buy', 'invest', 'opportunity', 'profitable', 'growth', 'rising',
            'affordable', 'value', 'deal', 'recommended', 'bullish', 'optimistic',
            'beautiful', 'spacious', 'convenient', 'prime', 'luxury', 'modern'
        ]
        
        negative_keywords = [
            'bad', 'terrible', 'awful', 'horrible', 'disappointing', 'overpriced',
            'expensive', 'risky', 'avoid', 'falling', 'crash', 'bubble',
            'bearish', 'pessimistic', 'declining', 'loss', 'fraud', 'scam',
            'small', 'cramped', 'noisy', 'traffic', 'pollution', 'old'
        ]
        
        positive_score = sum(1 for word in positive_keywords if word in text_lower)
        negative_score = sum(1 for word in negative_keywords if word in text_lower)
        
        if positive_score > negative_score:
            sentiment = 'Positive'
            score = min(0.8, 0.3 + (positive_score * 0.1))
        elif negative_score > positive_score:
            sentiment = 'Negative' 
            score = max(-0.8, -0.3 - (negative_score * 0.1))
        else:
            sentiment = 'Neutral'
            score = 0.0
        
        confidence = min(0.6, abs(positive_score - negative_score) * 0.15)
        
        return {
            'sentiment': sentiment,
            'score': score,
            'confidence': confidence,
            'reason': f'Keyword-based analysis (P:{positive_score}, N:{negative_score})',
            'analysis_type': 'fallback'
        }
    
    def analyze_combined_data(self, scraped_data: Dict[str, List[Dict]], location: str) -> Dict:
        """Analyze combined data from all sources with comprehensive insights"""
        if not scraped_data:
            return {'error': 'No data provided'}
        
        try:
            # Flatten all data
            all_texts = []
            source_data = {}
            
            for source, data_list in scraped_data.items():
                source_texts = [item['text'] for item in data_list if item.get('text')]
                all_texts.extend(source_texts)
                source_data[source] = source_texts
            
            if not all_texts:
                return {'error': 'No text data found'}
            
            # Get market context
            market_context = self.analyze_market_context(location)
            
            # Perform batch sentiment analysis
            sentiment_results = self.analyze_sentiment_batch(all_texts, location)
            
            # Calculate comprehensive metrics
            total_items = len(sentiment_results)
            positive_count = sum(1 for r in sentiment_results if r['sentiment'] == 'Positive')
            negative_count = sum(1 for r in sentiment_results if r['sentiment'] == 'Negative')
            neutral_count = total_items - positive_count - negative_count
            
            avg_score = sum(r['score'] for r in sentiment_results) / total_items if total_items > 0 else 0
            avg_confidence = sum(r['confidence'] for r in sentiment_results) / total_items if total_items > 0 else 0
            
            # Source-wise analysis
            source_analysis = {}
            start_idx = 0
            
            for source, texts in source_data.items():
                end_idx = start_idx + len(texts)
                source_results = sentiment_results[start_idx:end_idx]
                
                if source_results:
                    source_avg = sum(r['score'] for r in source_results) / len(source_results)
                    source_positive = sum(1 for r in source_results if r['sentiment'] == 'Positive')
                    
                    source_analysis[source] = {
                        'count': len(source_results),
                        'avg_score': source_avg,
                        'positive_count': source_positive,
                        'positive_ratio': source_positive / len(source_results),
                        'sentiment_distribution': {
                            'Positive': sum(1 for r in source_results if r['sentiment'] == 'Positive'),
                            'Negative': sum(1 for r in source_results if r['sentiment'] == 'Negative'),
                            'Neutral': sum(1 for r in source_results if r['sentiment'] == 'Neutral')
                        }
                    }
                
                start_idx = end_idx
            
            # Advanced sentiment analysis
            if self.claude_client:
                comprehensive_analysis = self._generate_comprehensive_report(
                    sentiment_results, source_analysis, market_context, location
                )
            else:
                comprehensive_analysis = self._generate_basic_report(
                    sentiment_results, source_analysis, location
                )
            
            return {
                'location': location,
                'analysis_timestamp': datetime.now().isoformat(),
                'total_items_analyzed': total_items,
                'overall_metrics': {
                    'positive_count': positive_count,
                    'negative_count': negative_count,
                    'neutral_count': neutral_count,
                    'positive_ratio': positive_count / total_items if total_items > 0 else 0,
                    'negative_ratio': negative_count / total_items if total_items > 0 else 0,
                    'average_sentiment_score': avg_score,
                    'average_confidence': avg_confidence,
                    'overall_sentiment': 'Positive' if avg_score > 0.1 else 'Negative' if avg_score < -0.1 else 'Neutral'
                },
                'source_analysis': source_analysis,
                'market_context': market_context,
                'comprehensive_analysis': comprehensive_analysis,
                'detailed_results': sentiment_results
            }
        
        except Exception as e:
            logger.error(f"Error in combined data analysis: {e}")
            return {'error': f'Analysis failed: {str(e)}'}
    
    def _generate_comprehensive_report(self, sentiment_results: List[Dict], 
                                     source_analysis: Dict, market_context: Dict, 
                                     location: str) -> Dict:
        """Generate comprehensive analysis report using Claude"""
        try:
            # Prepare data summary for Claude
            summary_data = {
                'total_items': len(sentiment_results),
                'avg_score': sum(r['score'] for r in sentiment_results) / len(sentiment_results),
                'sentiment_distribution': {
                    'positive': sum(1 for r in sentiment_results if r['sentiment'] == 'Positive'),
                    'negative': sum(1 for r in sentiment_results if r['sentiment'] == 'Negative'),
                    'neutral': sum(1 for r in sentiment_results if r['sentiment'] == 'Neutral')
                },
                'source_breakdown': source_analysis,
                'market_context': market_context
            }
            
            # Get sample texts for context
            sample_positive = [r['reason'] for r in sentiment_results if r['sentiment'] == 'Positive'][:3]
            sample_negative = [r['reason'] for r in sentiment_results if r['sentiment'] == 'Negative'][:3]
            
            analysis_prompt = f"""
As a real estate market analyst, provide a comprehensive analysis report for {location} based on the following sentiment analysis data:

Data Summary:
{json.dumps(summary_data, indent=2)}

Sample Positive Sentiments:
{'; '.join(sample_positive)}

Sample Negative Sentiments:
{'; '.join(sample_negative)}

Please provide a detailed JSON analysis with:
{{
    "executive_summary": "Brief overview of sentiment findings",
    "market_sentiment_assessment": "Detailed market sentiment analysis",
    "key_insights": ["insight1", "insight2", "insight3"],
    "trends_identified": ["trend1", "trend2", "trend3"],
    "risk_factors": ["risk1", "risk2"],
    "opportunities": ["opp1", "opp2"], 
    "investment_recommendation": "Buy/Hold/Sell/Wait",
    "confidence_level": "High/Medium/Low",
    "price_outlook": "Bullish/Bearish/Neutral",
    "market_timing": "Good/Poor/Neutral",
    "source_reliability": {{"source1": "High/Medium/Low"}},
    "action_items": ["action1", "action2"],
    "monitoring_points": ["point1", "point2"]
}}
"""
            
            response = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",  # Updated to current model
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": analysis_prompt
                }]
            )
            
            return json.loads(response.content[0].text)
        
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {e}")
            return self._generate_basic_report(sentiment_results, source_analysis, location)
    
    def _generate_basic_report(self, sentiment_results: List[Dict], 
                             source_analysis: Dict, location: str) -> Dict:
        """Generate basic analysis report as fallback"""
        total_items = len(sentiment_results)
        avg_score = sum(r['score'] for r in sentiment_results) / total_items if total_items > 0 else 0
        
        positive_count = sum(1 for r in sentiment_results if r['sentiment'] == 'Positive')
        negative_count = sum(1 for r in sentiment_results if r['sentiment'] == 'Negative')
        
        if avg_score > 0.2:
            overall_assessment = "Positive market sentiment detected"
            recommendation = "Consider buying opportunities"
        elif avg_score < -0.2:
            overall_assessment = "Negative market sentiment detected"
            recommendation = "Exercise caution, wait for better timing"
        else:
            overall_assessment = "Neutral market sentiment"
            recommendation = "Monitor market closely"
        
        # Identify best and worst performing sources
        best_source = max(source_analysis.keys(), 
                         key=lambda x: source_analysis[x]['avg_score']) if source_analysis else None
        worst_source = min(source_analysis.keys(), 
                          key=lambda x: source_analysis[x]['avg_score']) if source_analysis else None
        
        return {
            "executive_summary": f"Analysis of {total_items} items shows {overall_assessment.lower()}",
            "market_sentiment_assessment": overall_assessment,
            "key_insights": [
                f"Overall sentiment score: {avg_score:.2f}",
                f"Positive mentions: {positive_count} ({positive_count/total_items*100:.1f}%)",
                f"Most positive source: {best_source}" if best_source else "No source data"
            ],
            "trends_identified": [
                "Sentiment analysis completed",
                "Multi-source data aggregated",
                "Basic trend analysis performed"
            ],
            "investment_recommendation": recommendation,
            "confidence_level": "Medium",
            "price_outlook": "Neutral",
            "market_timing": "Monitor",
            "source_reliability": {source: "Medium" for source in source_analysis.keys()},
            "action_items": [
                "Continue monitoring sentiment trends",
                "Gather more market data"
            ]
        }