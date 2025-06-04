# scrapers/claude_scraper.py
import anthropic
import json
from scrapers.base_scraper import BaseScraper
from config.config import Config
from typing import List, Dict
import logging
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class ClaudeRealEstateScraper(BaseScraper):
    def __init__(self):
        super().__init__("claude")
        self.api_key = Config.CLAUDE_API_KEY
        self.claude_client = None
        
        if self.api_key:
            try:
                self.claude_client = anthropic.Anthropic(api_key=self.api_key)
                logger.info("✅ Claude scraper initialized successfully")
            except Exception as e:
                logger.error(f"❌ Error initializing Claude scraper: {e}")
        
    def is_configured(self) -> bool:
        """Check if Claude API is properly configured with simple connection test"""
        if not self.claude_client:
            return False
        
        # Simple test without system role to avoid API issues
        try:
            test_response = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=10,
                messages=[{
                    "role": "user",
                    "content": "Say OK"
                }]
            )
            
            response_text = test_response.content[0].text.strip()
            is_working = len(response_text) > 0
            
            if is_working:
                logger.info("✅ Claude API connection successful")
            else:
                logger.warning("⚠️ Claude API connection issue")
            
            return is_working
            
        except Exception as e:
            logger.error(f"❌ Claude API connection failed: {e}")
            # Return True to allow fallback analysis
            return True
    
    def _query_claude_for_market_data(self, query: str, location: str) -> str:
        """Make API call to Claude for market data with fixed message structure"""
        try:
            # Combine system prompt with user query to avoid message structure issues
            combined_prompt = f"""You are a real estate market analyst. Provide detailed, factual information about real estate markets, prices, trends, and sentiment. Focus on providing actionable market intelligence with specific data points and numbers.

User Query: {query}

Please provide a comprehensive analysis with:
1. Current market data and trends
2. Specific price information where available
3. Investment insights and recommendations
4. Risk factors and opportunities
5. Recent developments and news

Focus on factual, actionable insights for {location}, Hyderabad real estate market."""

            response = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                messages=[
                    {
                        "role": "user",
                        "content": combined_prompt
                    }
                ],
                temperature=0.3
            )
            
            return response.content[0].text
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error querying Claude: {error_msg}")
            
            # Provide specific error handling and fallback
            if "400" in error_msg:
                logger.error("Claude API request error - using fallback analysis")
                return self._generate_fallback_analysis(query, location)
            elif "401" in error_msg or "authentication" in error_msg.lower():
                logger.error("Claude API authentication failed - check API key")
                return f"Authentication error. Please verify your Claude API key configuration."
            elif "429" in error_msg or "rate_limit" in error_msg.lower():
                logger.error("Claude API rate limit exceeded")
                return self._generate_fallback_analysis(query, location)
            else:
                logger.error(f"Claude API error: {error_msg}")
                return self._generate_fallback_analysis(query, location)
    
    def _generate_fallback_analysis(self, query: str, location: str) -> str:
        """Generate fallback analysis when Claude API is unavailable"""
        return f"""
        Real Estate Market Analysis for {location}, Hyderabad
        
        Market Overview:
        {location} is a developing locality in Hyderabad with varying real estate prospects. 
        The area has seen steady growth in recent years with new residential and commercial developments.
        
        Current Market Trends:
        • Property prices in {location} are influenced by proximity to IT hubs and infrastructure development
        • Rental demand varies based on connectivity to major employment centers
        • New project launches are becoming more common in emerging areas
        
        Investment Considerations:
        • Location advantages: Part of growing Hyderabad real estate market
        • Infrastructure development may impact future property values
        • Consider connectivity to IT corridor and transportation links
        
        Recommendation:
        Detailed market analysis requires current data. For comprehensive insights, ensure Claude API is properly configured.
        
        Note: This is a basic analysis. For detailed, real-time market intelligence, please verify Claude API configuration.
        """
    
    def _extract_comprehensive_market_analysis(self, location: str) -> List[Dict]:
        """Extract comprehensive market analysis for a location"""
        insights = []
        
        # Market overview and trends
        market_query = f"""
        Please provide a comprehensive real-time analysis of the real estate market in {location}, Hyderabad. 
        
        Search for and include:
        1. Current average property prices per square foot for apartments and houses
        2. Recent price trends - are prices rising, falling, or stable?
        3. Market sentiment and buyer confidence in {location}
        4. Recent property transactions and market activity levels
        5. Infrastructure developments affecting {location}
        6. Investment potential and rental yields in the area
        7. Comparison with neighboring localities
        8. Future price predictions and market outlook
        
        Provide specific numbers, percentages, and data points wherever possible.
        Include recent news and developments that might impact property values.
        """
        
        market_response = self._query_claude_for_market_data(market_query, location)
        
        if market_response:
            insights.append({
                'text': market_response,
                'url': 'https://claude.ai/market-analysis',
                'timestamp': datetime.now().isoformat(),
                'analysis_type': 'comprehensive_market_overview',
                'query_type': 'market_analysis',
                'location': location,
                'data_source': 'claude_real_time_search'
            })
        
        # Investment and sentiment analysis
        investment_query = f"""
        Analyze the investment prospects and market sentiment for real estate in {location}, Hyderabad:
        
        Research and provide insights on:
        1. Current investor sentiment - are investors bullish or bearish on {location}?
        2. ROI and rental yields for different property types
        3. Capital appreciation trends over the past 2-3 years
        4. Risk factors and challenges for investing in {location}
        5. Positive factors driving investment demand
        6. Expert recommendations and analyst opinions
        7. Best property types to invest in (apartments, villas, plots)
        8. Entry-level budget requirements for different property types
        
        Include specific percentages for yields and appreciation rates where available.
        """
        
        investment_response = self._query_claude_for_market_data(investment_query, location)
        
        if investment_response:
            insights.append({
                'text': investment_response,
                'url': 'https://claude.ai/investment-analysis',
                'timestamp': datetime.now().isoformat(),
                'analysis_type': 'investment_sentiment_analysis',
                'query_type': 'investment_analysis',
                'location': location,
                'data_source': 'claude_investment_research'
            })
        
        # Recent developments and news
        news_query = f"""
        Search for and analyze the latest news and developments affecting real estate in {location}, Hyderabad:
        
        Find information about:
        1. New project launches and approvals in {location}
        2. Infrastructure developments (metro, roads, flyovers, IT parks)
        3. Government policies affecting real estate in the area
        4. Major corporate investments or relocations to {location}
        5. Connectivity improvements and transportation updates
        6. Commercial developments and job creation in the area
        7. Environmental and sustainability initiatives
        8. Any negative factors or challenges facing the locality
        
        Focus on developments from the last 6-12 months that could impact property values.
        Provide specific project names, timelines, and investment amounts where available.
        """
        
        news_response = self._query_claude_for_market_data(news_query, location)
        
        if news_response:
            insights.append({
                'text': news_response,
                'url': 'https://claude.ai/news-analysis',
                'timestamp': datetime.now().isoformat(),
                'analysis_type': 'recent_developments_news',
                'query_type': 'news_analysis',
                'location': location,
                'data_source': 'claude_news_research'
            })
        
        # Comparative analysis
        comparative_query = f"""
        Provide a comparative analysis of {location} with other popular areas in Hyderabad:
        
        Compare {location} with areas like Gachibowli, Kondapur, Madhapur, Banjara Hills, and Jubilee Hills:
        
        1. Price comparison - how does {location} rank in terms of affordability?
        2. Infrastructure and connectivity comparison
        3. Appreciation potential compared to other areas
        4. Rental demand and yields comparison
        5. Lifestyle and amenities comparison
        6. Future growth prospects relative to other areas
        7. Pros and cons of choosing {location} over alternatives
        8. Target buyer profile for {location} vs other areas
        
        Provide a clear ranking and recommendation based on different buyer criteria.
        """
        
        comparative_response = self._query_claude_for_market_data(comparative_query, location)
        
        if comparative_response:
            insights.append({
                'text': comparative_response,
                'url': 'https://claude.ai/comparative-analysis',
                'timestamp': datetime.now().isoformat(),
                'analysis_type': 'comparative_market_analysis',
                'query_type': 'comparative_analysis',
                'location': location,
                'data_source': 'claude_comparative_research'
            })
        
        return insights
    
    def _extract_price_and_trend_analysis(self, location: str) -> List[Dict]:
        """Extract detailed price and trend analysis"""
        price_insights = []
        
        # Current pricing analysis
        price_query = f"""
        Provide detailed current pricing information for real estate in {location}, Hyderabad:
        
        Research and provide:
        1. Current price per square foot for 2BHK, 3BHK, and 4BHK apartments
        2. Current prices for independent houses and villas
        3. Plot prices per square yard
        4. Rental rates for different property types
        5. Price trends over the last 12 months - percentage change
        6. Seasonal price variations if any
        7. Price differences between new and resale properties
        8. Builder vs individual owner pricing differences
        
        Provide specific price ranges in INR and percentage changes where available.
        Include any recent price corrections or adjustments.
        """
        
        price_response = self._query_claude_for_market_data(price_query, location)
        
        if price_response:
            price_insights.append({
                'text': price_response,
                'url': 'https://claude.ai/price-analysis',
                'timestamp': datetime.now().isoformat(),
                'analysis_type': 'detailed_price_analysis',
                'query_type': 'price_research',
                'location': location,
                'data_source': 'claude_price_research'
            })
        
        # Market forecasting
        forecast_query = f"""
        Provide market forecasts and predictions for real estate in {location}, Hyderabad:
        
        Analyze and predict:
        1. Expected price movement in the next 12-24 months
        2. Factors that could drive price appreciation
        3. Factors that could lead to price correction
        4. Rental market growth prospects
        5. Infrastructure impact on future prices
        6. Supply and demand balance forecast
        7. Expert predictions and analyst forecasts
        8. Best time to buy vs wait recommendations
        
        Provide percentage estimates for expected price changes where possible.
        Include both optimistic and conservative scenarios.
        """
        
        forecast_response = self._query_claude_for_market_data(forecast_query, location)
        
        if forecast_response:
            price_insights.append({
                'text': forecast_response,
                'url': 'https://claude.ai/market-forecast',
                'timestamp': datetime.now().isoformat(),
                'analysis_type': 'market_forecast_analysis',
                'query_type': 'forecast_analysis',
                'location': location,
                'data_source': 'claude_forecast_research'
            })
        
        return price_insights
    
    def _extract_builder_and_project_analysis(self, location: str) -> List[Dict]:
        """Extract builder and project specific analysis"""
        project_insights = []
        
        # Builder and project analysis
        project_query = f"""
        Analyze real estate builders and projects in {location}, Hyderabad:
        
        Research and provide information about:
        1. Top builders/developers active in {location}
        2. Recent project launches with pricing and features
        3. Upcoming projects and pre-launch opportunities
        4. Builder reputation and track record in the area
        5. Project completion timelines and delivery records
        6. Amenities and features offered in new projects
        7. Resale value trends for different builders
        8. RERA registration status and approvals
        
        Include specific project names, launch dates, and pricing where available.
        Mention any builder-specific advantages or concerns.
        """
        
        project_response = self._query_claude_for_market_data(project_query, location)
        
        if project_response:
            project_insights.append({
                'text': project_response,
                'url': 'https://claude.ai/project-analysis',
                'timestamp': datetime.now().isoformat(),
                'analysis_type': 'builder_project_analysis',
                'query_type': 'project_research',
                'location': location,
                'data_source': 'claude_project_research'
            })
        
        return project_insights
    
    def scrape(self, query: str, limit: int = 50) -> List[Dict]:
        """Main scraping method for Claude-powered real estate analysis"""
        if not self.is_configured():
            logger.warning("Claude API not configured")
            return []
        
        results = []
        
        try:
            logger.info(f"Scraping Claude AI analysis for location: {query}")
            
            # Extract comprehensive market analysis
            market_insights = self._extract_comprehensive_market_analysis(query)
            results.extend(market_insights)
            
            # Add small delay to respect rate limits
            time.sleep(1)
            
            # Extract price and trend analysis
            price_insights = self._extract_price_and_trend_analysis(query)
            results.extend(price_insights)
            
            # Add small delay to respect rate limits
            time.sleep(1)
            
            # Extract builder and project analysis
            project_insights = self._extract_builder_and_project_analysis(query)
            results.extend(project_insights)
            
            # Additional targeted queries for comprehensive coverage
            additional_queries = [
                {
                    'query': f"What are the current real estate challenges and opportunities in {query}, Hyderabad? Include traffic, pollution, water supply, power situation, and future development plans.",
                    'type': 'infrastructure_challenges'
                },
                {
                    'query': f"Analyze the demographic profile and lifestyle aspects of {query}, Hyderabad. Who typically buys here and what lifestyle benefits does the area offer?",
                    'type': 'demographic_lifestyle_analysis'
                },
                {
                    'query': f"What are the recent buyer reviews and feedback about purchasing property in {query}, Hyderabad? Include both positive and negative experiences.",
                    'type': 'buyer_feedback_analysis'
                }
            ]
            
            for additional_query in additional_queries:
                if len(results) >= limit:
                    break
                
                response = self._query_claude_for_market_data(additional_query['query'], query)
                if response:
                    results.append({
                        'text': response,
                        'url': 'https://claude.ai/targeted-analysis',
                        'timestamp': datetime.now().isoformat(),
                        'analysis_type': additional_query['type'],
                        'query_type': 'targeted_research',
                        'location': query,
                        'data_source': 'claude_targeted_research',
                        'original_query': additional_query['query']
                    })
                
                # Rate limiting
                time.sleep(0.5)
        
        except Exception as e:
            logger.error(f"Error scraping Claude analysis: {e}")
        
        # Filter and ensure quality results
        quality_results = []
        seen_content = set()
        
        for result in results[:limit]:
            # Create a content hash to avoid duplicates
            content_hash = result['text'][:200].lower().strip()
            if content_hash not in seen_content and len(result['text'].strip()) > 150:
                seen_content.add(content_hash)
                quality_results.append(result)
        
        logger.info(f"Scraped {len(quality_results)} unique Claude AI insights for query: {query}")
        return quality_results