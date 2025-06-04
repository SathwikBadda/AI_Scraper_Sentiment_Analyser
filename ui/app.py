# ui/app.py
"""
Enhanced Real Estate Sentiment Analysis - Complete Application
Comprehensive real estate sentiment analysis with Instagram, Claude AI, and multi-source data
"""

import sys
import os
from pathlib import Path

# Fix Python path
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import logging
from datetime import datetime, timedelta
import time
import json
from typing import List, Dict
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

# Configure page
st.set_page_config(
    page_title="Enhanced Real Estate Sentiment Analysis",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ================================
# COMPONENT INITIALIZATION
# ================================

@st.cache_resource
def initialize_components():
    """Initialize all system components with comprehensive error handling"""
    components = {}
    
    # Initialize Database
    try:
        from database.operations import DatabaseOperations
        components['db_ops'] = DatabaseOperations()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization error: {e}")
        components['db_ops'] = None
    
    # Initialize Configuration
    try:
        from config.config import Config
        components['config'] = Config
        components['config_validation'] = Config.validate_config()
        logger.info("✅ Configuration loaded successfully")
    except Exception as e:
        logger.error(f"❌ Configuration loading error: {e}")
        components['config'] = None
        components['config_validation'] = {}
    
    # Initialize Scrapers
    components['scrapers'] = {}
    
    scrapers_config = [
        ('news', 'scrapers.news_scraper', 'NewsScraper', '📰', 'News Articles'),
        ('youtube', 'scrapers.youtube_scraper', 'YouTubeScraper', '🎥', 'YouTube Comments'),
        ('reddit', 'scrapers.reddit_scraper', 'RedditScraper', '🔗', 'Reddit Discussions'),
        ('twitter', 'scrapers.twitter_scraper', 'TwitterScraper', '🐦', 'Twitter Posts'),
        ('instagram', 'scrapers.instagram_scraper', 'InstagramScraper', '📱', 'Instagram Data'),
        ('claude', 'scrapers.claude_scraper', 'ClaudeRealEstateScraper', '🤖', 'Claude AI Analysis'),
    ]
    
    for name, module_path, class_name, icon, display_name in scrapers_config:
        try:
            module = __import__(module_path, fromlist=[class_name])
            scraper_class = getattr(module, class_name)
            scraper_instance = scraper_class()
            
            # Check configuration status
            is_configured = True
            if hasattr(scraper_instance, 'is_configured'):
                is_configured = scraper_instance.is_configured()
            
            components['scrapers'][name] = {
                'instance': scraper_instance,
                'icon': icon,
                'name': display_name,
                'status': 'ready' if is_configured else 'not_configured',
                'configured': is_configured,
                'error': None
            }
            
            status = "configured" if is_configured else "not configured"
            logger.info(f"✅ {display_name} scraper loaded ({status})")
            
        except Exception as e:
            logger.warning(f"⚠️ {display_name} scraper initialization failed: {e}")
            components['scrapers'][name] = {
                'instance': None,
                'icon': icon,
                'name': display_name,
                'status': 'error',
                'configured': False,
                'error': str(e)
            }
    
    # Initialize Processing Components
    try:
        from preprocessing.cleaner import TextCleaner
        from preprocessing.location_extractor import LocationExtractor
        from preprocessing.claude_sentiment_analyzer import EnhancedSentimentAnalyzer
        
        components['cleaner'] = TextCleaner()
        components['location_extractor'] = LocationExtractor()
        components['sentiment_analyzer'] = EnhancedSentimentAnalyzer()
        components['claude_configured'] = components['sentiment_analyzer'].is_configured()
        
        logger.info(f"✅ Processing components loaded (Claude: {'✅' if components['claude_configured'] else '❌'})")
        
    except Exception as e:
        logger.error(f"❌ Processing components initialization error: {e}")
        components['cleaner'] = None
        components['location_extractor'] = None
        components['sentiment_analyzer'] = None
        components['claude_configured'] = False
    
    return components

# ================================
# DATA SCRAPING FUNCTIONS
# ================================

def scrape_source_data(source_name: str, scraper_info: dict, location: str, components: dict, limit: int = 30) -> List[Dict]:
    """Scrape data from a single source with comprehensive processing"""
    results = []
    
    if not scraper_info['instance'] or not scraper_info['configured']:
        return results
    
    try:
        scraper = scraper_info['instance']
        
        # Create progress indicators
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0, text=f"🔍 Initializing {scraper_info['name']}...")
            
            # Step 1: Fetch raw data
            progress_bar.progress(0.2, text=f"📥 Fetching data from {scraper_info['name']}...")
            raw_data = scraper.scrape(location, limit=limit)
            
            if not raw_data:
                progress_bar.progress(1.0, text=f"⚪ No data found from {scraper_info['name']}")
                time.sleep(0.5)
                progress_container.empty()
                return results
            
            # Step 2: Process each item
            progress_bar.progress(0.4, text=f"⚙️ Processing {len(raw_data)} items...")
            
            for i, item in enumerate(raw_data):
                try:
                    # Extract location information
                    extracted_location = location
                    if components['location_extractor']:
                        extracted_loc = components['location_extractor'].extract_location(item['text'])
                        if extracted_loc:
                            extracted_location = extracted_loc
                    
                    # Clean text
                    clean_text = item['text']
                    if components['cleaner']:
                        clean_text = components['cleaner'].clean_text(item['text'])
                    
                    # Perform sentiment analysis
                    sentiment_result = {
                        'sentiment': 'Neutral', 
                        'score': 0.0, 
                        'reason': 'No analysis available', 
                        'confidence': 0.0,
                        'analysis_type': 'basic'
                    }
                    
                    if components['sentiment_analyzer']:
                        if components['claude_configured'] and source_name in ['instagram', 'claude']:
                            # Enhanced Claude analysis for premium sources
                            sentiment_result = components['sentiment_analyzer'].analyze_sentiment(item['text'], location)
                        else:
                            # Basic analysis for other sources
                            sentiment_result = components['sentiment_analyzer']._fallback_single_analysis(item['text'])
                    
                    # Prepare processed item
                    processed_item = {
                        'source': source_name,
                        'location': extracted_location,
                        'raw_text': item['text'][:1000],  # Limit for storage
                        'clean_text': clean_text[:500],
                        'sentiment': sentiment_result['sentiment'],
                        'score': sentiment_result['score'],
                        'confidence': sentiment_result.get('confidence', 0.0),
                        'reason': sentiment_result['reason'],
                        'analysis_type': sentiment_result.get('analysis_type', 'basic'),
                        'timestamp': item.get('timestamp', datetime.now().isoformat()),
                        'url': item.get('url', ''),
                        'metadata': {
                            'source_type': source_name,
                            'processing_time': datetime.now().isoformat(),
                            **item.get('metadata', {})
                        }
                    }
                    
                    # Add source-specific metadata
                    if source_name == 'instagram':
                        processed_item['metadata'].update({
                            'likes': item.get('likes', 0),
                            'comments_count': item.get('comments_count', 0),
                            'content_type': item.get('content_type', 'post'),
                            'username': item.get('username', ''),
                            'media_type': item.get('media_type', 'text')
                        })
                    elif source_name == 'claude':
                        processed_item['metadata'].update({
                            'query_type': item.get('query_type', 'general'),
                            'analysis_type': item.get('analysis_type', 'market_analysis'),
                            'data_source': item.get('data_source', 'claude_research')
                        })
                    
                    results.append(processed_item)
                    
                    # Store in database
                    if components['db_ops']:
                        try:
                            db_data = {
                                'source': source_name,
                                'location': extracted_location,
                                'raw_text': item['text'][:1000],
                                'clean_text': clean_text[:500],
                                'sentiment': sentiment_result['sentiment'],
                                'reason': sentiment_result['reason'],
                                'score': sentiment_result['score']
                            }
                            components['db_ops'].insert_sentiment_data(db_data)
                        except Exception as db_error:
                            logger.warning(f"Database storage error: {db_error}")
                    
                    # Update progress
                    item_progress = 0.4 + (0.5 * (i + 1) / len(raw_data))
                    progress_bar.progress(item_progress, text=f"⚙️ Processed {i+1}/{len(raw_data)} items")
                    
                except Exception as item_error:
                    logger.error(f"Error processing item from {source_name}: {item_error}")
                    continue
            
            # Completion
            progress_bar.progress(1.0, text=f"✅ {scraper_info['name']}: {len(results)} items processed")
            time.sleep(0.5)
            progress_container.empty()
    
    except Exception as e:
        logger.error(f"Error scraping {source_name}: {e}")
        st.error(f"❌ Error scraping {scraper_info['name']}: {str(e)}")
    
    return results

def perform_comprehensive_analysis(scraped_data: Dict[str, List[Dict]], location: str, components: dict) -> Dict:
    """Perform comprehensive analysis using Claude AI"""
    
    if not scraped_data or not components['sentiment_analyzer']:
        return {}
    
    try:
        if components['claude_configured']:
            with st.spinner("🤖 Performing comprehensive Claude AI analysis..."):
                analysis = components['sentiment_analyzer'].analyze_combined_data(scraped_data, location)
                return analysis
        else:
            # Basic fallback analysis
            all_data = []
            for source_data in scraped_data.values():
                all_data.extend(source_data)
            
            if not all_data:
                return {}
            
            df = pd.DataFrame(all_data)
            total_items = len(all_data)
            avg_score = df['score'].mean()
            sentiment_counts = df['sentiment'].value_counts().to_dict()
            
            return {
                'location': location,
                'analysis_timestamp': datetime.now().isoformat(),
                'total_items_analyzed': total_items,
                'overall_metrics': {
                    'average_sentiment_score': avg_score,
                    'sentiment_distribution': sentiment_counts,
                    'overall_sentiment': 'Positive' if avg_score > 0.1 else 'Negative' if avg_score < -0.1 else 'Neutral'
                },
                'comprehensive_analysis': {
                    'executive_summary': f"Basic analysis of {total_items} items shows {('positive' if avg_score > 0 else 'negative' if avg_score < 0 else 'neutral')} sentiment",
                    'investment_recommendation': 'Detailed analysis requires Claude AI configuration',
                    'confidence_level': 'Low (basic analysis)',
                    'key_insights': [f"Total items: {total_items}", f"Average score: {avg_score:.2f}"]
                }
            }
    
    except Exception as e:
        logger.error(f"Error in comprehensive analysis: {e}")
        return {}

# ================================
# VISUALIZATION FUNCTIONS
# ================================

def create_sentiment_pie_chart(sentiment_counts: dict, title: str = "Sentiment Distribution"):
    """Create enhanced pie chart for sentiment distribution"""
    if not sentiment_counts:
        return None
    
    fig = px.pie(
        values=list(sentiment_counts.values()),
        names=list(sentiment_counts.keys()),
        color_discrete_map={
            'Positive': '#2E8B57',  # Sea Green
            'Negative': '#DC143C',  # Crimson
            'Neutral': '#4682B4'    # Steel Blue
        },
        hole=0.4,
        title=title
    )
    
    fig.update_traces(
        textposition='inside', 
        textinfo='percent+label',
        textfont_size=12
    )
    
    fig.update_layout(
        height=400,
        showlegend=True,
        title_font_size=16,
        font=dict(size=12)
    )
    
    return fig

def create_timeline_chart(df: pd.DataFrame, title: str = "Sentiment Timeline"):
    """Create timeline chart with proper error handling"""
    try:
        if 'timestamp' not in df.columns or df.empty:
            return create_fallback_histogram(df)
        
        # Parse timestamps with error handling
        df_copy = df.copy()
        df_copy['timestamp_parsed'] = pd.to_datetime(df_copy['timestamp'], errors='coerce')
        df_valid = df_copy.dropna(subset=['timestamp_parsed'])
        
        if df_valid.empty:
            return create_fallback_histogram(df)
        
        df_sorted = df_valid.sort_values('timestamp_parsed')
        
        fig = px.scatter(
            df_sorted,
            x='timestamp_parsed',
            y='score',
            color='sentiment',
            size='confidence',
            hover_data=['reason', 'source'],
            color_discrete_map={
                'Positive': '#2E8B57',
                'Negative': '#DC143C',
                'Neutral': '#4682B4'
            },
            title=title
        )
        
        fig.update_layout(
            height=400,
            xaxis_title="Time",
            yaxis_title="Sentiment Score",
            title_font_size=16
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error creating timeline chart: {e}")
        return create_fallback_histogram(df)

def create_fallback_histogram(df: pd.DataFrame, title: str = "Sentiment Score Distribution"):
    """Create fallback histogram when timeline fails"""
    if df.empty or 'score' not in df.columns:
        return None
    
    fig = px.histogram(
        df, 
        x='score', 
        nbins=15,
        title=title,
        color_discrete_sequence=['#4682B4']
    )
    
    fig.update_layout(
        height=400,
        xaxis_title="Sentiment Score",
        yaxis_title="Count",
        title_font_size=16
    )
    
    return fig

def create_source_comparison_chart(df: pd.DataFrame):
    """Create source comparison chart"""
    if df.empty or 'source' not in df.columns:
        return None
    
    # Create source-wise sentiment breakdown
    source_sentiment_data = []
    for source in df['source'].unique():
        source_df = df[df['source'] == source]
        for sentiment in ['Positive', 'Negative', 'Neutral']:
            count = len(source_df[source_df['sentiment'] == sentiment])
            if count > 0:
                source_sentiment_data.append({
                    'source': source.title(),
                    'sentiment': sentiment,
                    'count': count
                })
    
    if not source_sentiment_data:
        return None
    
    source_sentiment_df = pd.DataFrame(source_sentiment_data)
    
    fig = px.bar(
        source_sentiment_df,
        x='source',
        y='count',
        color='sentiment',
        color_discrete_map={
            'Positive': '#2E8B57',
            'Negative': '#DC143C',
            'Neutral': '#4682B4'
        },
        title="Sentiment Distribution by Source"
    )
    
    fig.update_layout(
        height=400,
        xaxis_title="Data Source",
        yaxis_title="Number of Items",
        title_font_size=16
    )
    
    return fig

# ================================
# UI COMPONENTS
# ================================

def display_header():
    """Display application header"""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%); 
                padding: 2rem; border-radius: 15px; margin-bottom: 2rem; 
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);">
        <h1 style="color: white; text-align: center; margin: 0; font-size: 2.8rem; font-weight: 700;">
            🏠 Enhanced Real Estate Sentiment Analysis
        </h1>
        <p style="color: white; text-align: center; margin: 1rem 0 0 0; font-size: 1.3rem; opacity: 0.9;">
            AI-Powered Real-time Sentiment Tracking for Hyderabad Property Market
        </p>
        <p style="color: rgba(255,255,255,0.8); text-align: center; margin: 0.5rem 0 0 0; font-size: 1rem;">
            📱 Instagram Data • 🤖 Claude AI Analysis • 📊 Multi-Source Intelligence
        </p>
    </div>
    """, unsafe_allow_html=True)

def display_system_status(components: dict):
    """Display system status in sidebar"""
    st.sidebar.header("🔧 System Status")
    
    # Overall system health
    scrapers = components['scrapers']
    total_scrapers = len(scrapers)
    configured_scrapers = sum(1 for s in scrapers.values() if s['configured'])
    
    # Progress indicator
    progress_value = configured_scrapers / total_scrapers if total_scrapers > 0 else 0
    st.sidebar.progress(progress_value, text=f"Ready: {configured_scrapers}/{total_scrapers} sources")
    
    # Individual scraper status
    st.sidebar.subheader("📊 Data Sources")
    
    for name, scraper_info in scrapers.items():
        if scraper_info['configured']:
            status_color = "#28a745"  # Green
            status_icon = "✅"
            status_text = "Ready"
        elif scraper_info['status'] == 'error':
            status_color = "#dc3545"  # Red
            status_icon = "❌"
            status_text = "Error"
        else:
            status_color = "#ffc107"  # Yellow
            status_icon = "⚠️"
            status_text = "Not Configured"
        
        st.sidebar.markdown(f"""
        <div style="padding: 0.5rem; margin: 0.3rem 0; border-radius: 8px; 
                    border-left: 4px solid {status_color}; background-color: rgba(0,0,0,0.05);">
            <span style="font-size: 1.1rem;">{scraper_info['icon']} {status_icon}</span>
            <strong> {scraper_info['name']}</strong><br>
            <small style="color: {status_color};">{status_text}</small>
        </div>
        """, unsafe_allow_html=True)
    
    # Claude AI status
    st.sidebar.subheader("🤖 AI Analysis Engine")
    claude_status = components.get('claude_configured', False)
    
    if claude_status:
        st.sidebar.success("✅ Claude AI: Advanced analysis enabled")
    else:
        st.sidebar.warning("⚠️ Claude AI: Basic mode only")

def display_configuration_guide(components: dict):
    """Display configuration guide for missing components"""
    try:
        config = components.get('config')
        if not config:
            return
        
        missing_configs = config.get_missing_configs() if hasattr(config, 'get_missing_configs') else []
        
        if missing_configs:
            st.sidebar.subheader("⚙️ Setup Guide")
            st.sidebar.warning(f"Missing: {', '.join(missing_configs)}")
            
            # Essential setup guide
            setup_guides = {
                'claude': {
                    'name': 'Claude AI',
                    'description': 'Essential for sentiment analysis and web search',
                    'url': 'https://console.anthropic.com',
                    'env_var': 'CLAUDE_API_KEY'
                },
                'instagram': {
                    'name': 'Instagram',
                    'description': 'For social media real estate data',
                    'url': 'https://developers.facebook.com',
                    'env_var': 'INSTAGRAM_ACCESS_TOKEN'
                },
                'reddit': {
                    'name': 'Reddit',
                    'description': 'For community discussions',
                    'url': 'https://www.reddit.com/prefs/apps',
                    'env_var': 'REDDIT_CLIENT_ID'
                }
            }
            
            for component in missing_configs:
                if component in setup_guides:
                    guide = setup_guides[component]
                    with st.sidebar.expander(f"Setup {guide['name']}"):
                        st.write(f"**Purpose:** {guide['description']}")
                        st.write(f"**Get API Key:** {guide['url']}")
                        st.code(f"{guide['env_var']}=your_api_key_here")
        else:
            st.sidebar.success("✅ All systems configured!")
    
    except Exception as e:
        st.sidebar.error(f"Configuration error: {e}")

def display_location_selector():
    """Display location selection interface"""
    st.header("📍 Location Analysis")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Hyderabad localities
        localities = [
            'Kondapur', 'Gachibowli', 'Madhapur', 'Hitech City', 'Financial District',
            'Banjara Hills', 'Jubilee Hills', 'Kukatpally', 'Miyapur', 'Begumpet',
            'Secunderabad', 'Ameerpet', 'Somajiguda', 'Abids', 'Charminar',
            'Dilsukhnagar', 'Uppal', 'Kompally', 'Bachupally', 'Nizampet',
            'Manikonda', 'Kokapet', 'Nanakramguda', 'Raidurg', 'Chandanagar'
        ]
        
        location = st.selectbox(
            "Select Hyderabad locality:",
            options=localities,
            index=0,
            help="Choose a location for comprehensive real estate sentiment analysis"
        )
        
        # Custom location option
        custom_location = st.text_input(
            "Or enter custom location:",
            placeholder="Enter any Hyderabad area...",
            help="Specify any locality in Hyderabad for analysis"
        )
        
        if custom_location.strip():
            location = custom_location.strip()
    
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        scrape_button = st.button(
            "🚀 Start Analysis",
            type="primary",
            use_container_width=True,
            help="Begin comprehensive data collection and analysis"
        )
    
    return location, scrape_button

def display_overall_dashboard(scraped_data: Dict[str, List[Dict]]):
    """Display overall analysis dashboard"""
    if not scraped_data:
        return
    
    st.header("📊 Overall Analysis Dashboard")
    
    # Combine all data
    all_data = []
    for source_data in scraped_data.values():
        all_data.extend(source_data)
    
    if not all_data:
        st.info("No data available for analysis")
        return
    
    df_all = pd.DataFrame(all_data)
    
    # Key metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    total_items = len(all_data)
    sentiment_counts = df_all['sentiment'].value_counts().to_dict()
    avg_sentiment = df_all['score'].mean()
    avg_confidence = df_all['confidence'].mean()
    
    positive_count = sentiment_counts.get('Positive', 0)
    negative_count = sentiment_counts.get('Negative', 0)
    neutral_count = sentiment_counts.get('Neutral', 0)
    
    with col1:
        st.metric("📊 Total Items", total_items)
    
    with col2:
        st.metric("😊 Positive", positive_count, f"{positive_count/total_items*100:.1f}%")
    
    with col3:
        st.metric("😞 Negative", negative_count, f"{negative_count/total_items*100:.1f}%")
    
    with col4:
        st.metric("😐 Neutral", neutral_count, f"{neutral_count/total_items*100:.1f}%")
    
    with col5:
        delta_color = "normal" if avg_sentiment > 0 else "inverse" if avg_sentiment < 0 else "off"
        st.metric("📈 Avg Score", f"{avg_sentiment:.2f}", delta_color=delta_color)
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        # Sentiment pie chart
        pie_fig = create_sentiment_pie_chart(sentiment_counts, "Overall Sentiment Distribution")
        if pie_fig:
            st.plotly_chart(pie_fig, use_container_width=True)
    
    with col2:
        # Source comparison
        source_fig = create_source_comparison_chart(df_all)
        if source_fig:
            st.plotly_chart(source_fig, use_container_width=True)

def display_comprehensive_analysis(analysis: Dict):
    """Display comprehensive AI analysis results"""
    if not analysis:
        return
    
    st.header("🎯 Comprehensive AI Analysis")
    
    comp_analysis = analysis.get('comprehensive_analysis', {})
    overall_metrics = analysis.get('overall_metrics', {})
    
    # Executive Summary Card
    if comp_analysis.get('executive_summary'):
        st.markdown(f"""
        <div style="background: linear-gradient(45deg, #667eea 0%, #764ba2 100%); 
                    padding: 1.5rem; border-radius: 12px; margin: 1rem 0;
                    color: white; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
            <h3 style="margin: 0; color: white; font-size: 1.4rem;">📋 Executive Summary</h3>
            <p style="margin: 0.8rem 0 0 0; font-size: 1.1rem; line-height: 1.4;">
                {comp_analysis['executive_summary']}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Key Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_items = analysis.get('total_items_analyzed', 0)
        st.metric("📊 Items Analyzed", total_items)
    
    with col2:
        avg_score = overall_metrics.get('average_sentiment_score', 0)
        st.metric("📈 Average Score", f"{avg_score:.2f}")
    
    with col3:
        overall_sentiment = overall_metrics.get('overall_sentiment', 'Neutral')
        sentiment_emoji = "😊" if overall_sentiment == 'Positive' else "😞" if overall_sentiment == 'Negative' else "😐"
        st.metric("🎭 Market Mood", f"{sentiment_emoji} {overall_sentiment}")
    
    with col4:
        confidence = comp_analysis.get('confidence_level', 'Medium')
        st.metric("🎯 Analysis Confidence", confidence)
    
    # Investment Insights
    if comp_analysis.get('investment_recommendation'):
        st.subheader("💰 Investment Intelligence")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🎯 Recommendations:**")
            recommendation = comp_analysis.get('investment_recommendation', 'Monitor')
            price_outlook = comp_analysis.get('price_outlook', 'Neutral')
            market_timing = comp_analysis.get('market_timing', 'Neutral')
            
            st.markdown(f"""
            - **Action:** {recommendation}
            - **Price Outlook:** {price_outlook}  
            - **Market Timing:** {market_timing}
            """)
        
        with col2:
            st.markdown("**💡 Key Insights:**")
            insights = comp_analysis.get('key_insights', [])
            for insight in insights[:4]:
                st.markdown(f"• {insight}")
    
    # Risk and Opportunities
    col1, col2 = st.columns(2)
    
    with col1:
        risks = comp_analysis.get('risk_factors', [])
        if risks:
            st.subheader("⚠️ Risk Factors")
            for risk in risks[:3]:
                st.markdown(f"• {risk}")
    
    with col2:
        opportunities = comp_analysis.get('opportunities', [])
        if opportunities:
            st.subheader("🌟 Opportunities")
            for opp in opportunities[:3]:
                st.markdown(f"• {opp}")

def display_source_analysis(source_name: str, scraper_info: dict, data: List[Dict]):
    """Display detailed analysis for individual data source"""
    
    if not data:
        if scraper_info['configured']:
            st.info(f"No data available from {scraper_info['name']}. Try running the analysis again.")
        else:
            st.warning(f"{scraper_info['name']} is not configured. Check the setup guide in the sidebar.")
        return
    
    # Source metrics
    col1, col2, col3, col4 = st.columns(4)
    
    df = pd.DataFrame(data)
    total_items = len(data)
    avg_sentiment = df['score'].mean() if not df.empty else 0
    sentiment_counts = df['sentiment'].value_counts().to_dict() if not df.empty else {}
    avg_confidence = df['confidence'].mean() if not df.empty and 'confidence' in df.columns else 0
    
    with col1:
        st.metric("📊 Total Items", total_items)
    
    with col2:
        st.metric("📈 Avg Sentiment", f"{avg_sentiment:.2f}")
    
    with col3:
        st.metric("🎯 Avg Confidence", f"{avg_confidence:.2f}")
    
    with col4:
        if source_name == 'instagram':
            total_engagement = sum(item['metadata'].get('likes', 0) + item['metadata'].get('comments_count', 0) for item in data)
            st.metric("👥 Total Engagement", total_engagement)
        else:
            positive_pct = (sentiment_counts.get('Positive', 0) / total_items * 100) if total_items > 0 else 0
            st.metric("😊 Positive %", f"{positive_pct:.1f}%")
    
    # Visualizations
    if sentiment_counts:
        col1, col2 = st.columns(2)
        
        with col1:
            # Sentiment distribution
            pie_fig = create_sentiment_pie_chart(sentiment_counts, f"{scraper_info['name']} Sentiment")
            if pie_fig:
                st.plotly_chart(pie_fig, use_container_width=True)
        
        with col2:
            # Timeline or histogram
            timeline_fig = create_timeline_chart(df, f"{scraper_info['name']} Timeline")
            if timeline_fig:
                st.plotly_chart(timeline_fig, use_container_width=True)
    
    # Source-specific analysis
    if source_name == 'instagram':
        display_instagram_analysis(data)
    elif source_name == 'claude':
        display_claude_analysis(data)
    
    # Data table with filtering
    display_data_table(source_name, scraper_info, df)

def display_instagram_analysis(data: List[Dict]):
    """Display Instagram-specific analysis"""
    st.subheader("📱 Instagram Engagement Analysis")
    
    # Engagement metrics
    engagement_data = []
    for item in data:
        likes = item['metadata'].get('likes', 0)
        comments = item['metadata'].get('comments_count', 0)
        total_engagement = likes + comments
        
        if total_engagement > 0:
            engagement_data.append({
                'engagement': total_engagement,
                'likes': likes,
                'comments': comments,
                'sentiment_score': item['score'],
                'sentiment': item['sentiment'],
                'content_type': item['metadata'].get('content_type', 'post')
            })
    
    if engagement_data:
        col1, col2 = st.columns(2)
        
        with col1:
            # Engagement vs Sentiment
            eng_df = pd.DataFrame(engagement_data)
            
            fig_engagement = px.scatter(
                eng_df,
                x='engagement',
                y='sentiment_score',
                color='sentiment',
                size='engagement',
                hover_data=['content_type', 'likes', 'comments'],
                color_discrete_map={
                    'Positive': '#2E8B57',
                    'Negative': '#DC143C',
                    'Neutral': '#4682B4'
                },
                title="Engagement vs Sentiment"
            )
            fig_engagement.update_layout(height=350)
            st.plotly_chart(fig_engagement, use_container_width=True)
        
        with col2:
            # Content type distribution
            content_types = [item['metadata'].get('content_type', 'post') for item in data]
            content_counts = pd.Series(content_types).value_counts()
            
            fig_content = px.bar(
                x=content_counts.index,
                y=content_counts.values,
                color=content_counts.index,
                title="Content Type Distribution"
            )
            fig_content.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig_content, use_container_width=True)

def display_claude_analysis(data: List[Dict]):
    """Display Claude-specific analysis"""
    st.subheader("🤖 Claude AI Analysis Breakdown")
    
    # Analysis type distribution
    analysis_types = [item['metadata'].get('query_type', 'general') for item in data]
    analysis_counts = pd.Series(analysis_types).value_counts()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_analysis = px.bar(
            x=analysis_counts.values,
            y=analysis_counts.index,
            orientation='h',
            color=analysis_counts.index,
            title="Claude Analysis Types"
        )
        fig_analysis.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig_analysis, use_container_width=True)
    
    with col2:
        # Confidence distribution
        df = pd.DataFrame(data)
        if 'confidence' in df.columns:
            fig_conf = px.histogram(
                df, x='confidence', nbins=10,
                title="Claude AI Confidence Distribution",
                color_discrete_sequence=['#4682B4']
            )
            fig_conf.update_layout(height=350)
            st.plotly_chart(fig_conf, use_container_width=True)

def display_data_table(source_name: str, scraper_info: dict, df: pd.DataFrame):
    """Display filterable data table"""
    st.subheader("📋 Detailed Data Analysis")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        sentiment_filter = st.selectbox(
            "Filter by Sentiment:",
            ['All', 'Positive', 'Negative', 'Neutral'],
            key=f"sentiment_filter_{source_name}"
        )
    
    with col2:
        sort_options = ['Timestamp', 'Sentiment Score', 'Confidence']
        if source_name == 'instagram':
            sort_options.append('Engagement')
        
        sort_by = st.selectbox(
            "Sort by:",
            sort_options,
            key=f"sort_filter_{source_name}"
        )
    
    with col3:
        if source_name == 'instagram':
            content_filter = st.selectbox(
                "Content Type:",
                ['All', 'post', 'comment', 'reply'],
                key=f"content_filter_{source_name}"
            )
        elif source_name == 'claude':
            analysis_types = ['All'] + list(set(df['metadata'].apply(lambda x: x.get('query_type', 'general'))))
            analysis_filter = st.selectbox(
                "Analysis Type:",
                analysis_types,
                key=f"analysis_filter_{source_name}"
            )
    
    # Apply filters
    filtered_df = df.copy()
    
    if sentiment_filter != 'All':
        filtered_df = filtered_df[filtered_df['sentiment'] == sentiment_filter]
    
    if source_name == 'instagram' and 'content_filter' in locals() and content_filter != 'All':
        filtered_df = filtered_df[filtered_df['metadata'].apply(lambda x: x.get('content_type', 'post') == content_filter)]
    
    if source_name == 'claude' and 'analysis_filter' in locals() and analysis_filter != 'All':
        filtered_df = filtered_df[filtered_df['metadata'].apply(lambda x: x.get('query_type', 'general') == analysis_filter)]
    
    # Sort data
    try:
        if sort_by == 'Timestamp':
            filtered_df['timestamp_parsed'] = pd.to_datetime(filtered_df['timestamp'], errors='coerce')
            filtered_df = filtered_df.sort_values('timestamp_parsed', ascending=False, na_position='last')
        elif sort_by == 'Sentiment Score':
            filtered_df = filtered_df.sort_values('score', ascending=False)
        elif sort_by == 'Confidence':
            filtered_df = filtered_df.sort_values('confidence', ascending=False)
        elif sort_by == 'Engagement' and source_name == 'instagram':
            filtered_df['total_engagement'] = filtered_df['metadata'].apply(
                lambda x: x.get('likes', 0) + x.get('comments_count', 0)
            )
            filtered_df = filtered_df.sort_values('total_engagement', ascending=False)
    except Exception as e:
        logger.error(f"Error sorting data: {e}")
    
    # Display table
    if not filtered_df.empty:
        # Prepare display dataframe
        display_df = filtered_df.copy()
        
        # Format timestamp
        try:
            display_df['formatted_time'] = pd.to_datetime(display_df['timestamp'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M')
        except:
            display_df['formatted_time'] = display_df['timestamp'].astype(str)
        
        # Create preview text
        display_df['text_preview'] = display_df['raw_text'].str[:150] + '...'
        
        # Select columns for display
        base_columns = ['formatted_time', 'sentiment', 'score', 'confidence', 'text_preview']
        
        if source_name == 'instagram':
            display_df['engagement'] = display_df['metadata'].apply(
                lambda x: x.get('likes', 0) + x.get('comments_count', 0)
            )
            base_columns.insert(-1, 'engagement')
        
        # Style the dataframe
        def style_sentiment_row(row):
            if row['sentiment'] == 'Positive':
                return ['background-color: rgba(46, 139, 87, 0.1)'] * len(row)
            elif row['sentiment'] == 'Negative':
                return ['background-color: rgba(220, 20, 60, 0.1)'] * len(row)
            else:
                return ['background-color: rgba(70, 130, 180, 0.1)'] * len(row)
        
        final_display_df = display_df[base_columns]
        styled_df = final_display_df.style.apply(style_sentiment_row, axis=1)
        
        st.dataframe(styled_df, use_container_width=True, height=400)
        
        # Detailed item view
        if st.checkbox(f"Show detailed analysis for {scraper_info['name']}", key=f"show_detailed_{source_name}"):
            selected_idx = st.selectbox(
                "Select item for detailed view:",
                range(len(filtered_df)),
                format_func=lambda x: f"Item {x+1}: {filtered_df.iloc[x]['sentiment']} ({filtered_df.iloc[x]['score']:.2f})",
                key=f"select_detailed_{source_name}"
            )
            
            if selected_idx is not None:
                display_detailed_item_view(filtered_df.iloc[selected_idx], source_name)
    else:
        st.info("No data matches the selected filters")

def display_detailed_item_view(item: pd.Series, source_name: str):
    """Display detailed view of selected item"""
    tab1, tab2, tab3 = st.tabs(["📄 Content", "📊 Analysis", "🔗 Metadata"])
    
    with tab1:
        st.markdown("**Full Text:**")
        st.text_area("", value=item['raw_text'], height=200, disabled=True, key=f"full_text_{source_name}_{item.name}")
        
        if item.get('url'):
            st.markdown(f"**Source URL:** [View Original]({item['url']})")
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Sentiment:** {item['sentiment']}")
            st.markdown(f"**Score:** {item['score']:.3f}")
            st.markdown(f"**Confidence:** {item.get('confidence', 'N/A'):.3f}")
        
        with col2:
            st.markdown(f"**Location:** {item['location']}")
            st.markdown(f"**Source:** {item['source']}")
            st.markdown(f"**Analysis Type:** {item.get('analysis_type', 'N/A')}")
        
        st.markdown("**Analysis Reasoning:**")
        st.text_area("", value=item['reason'], height=100, disabled=True, key=f"reason_{source_name}_{item.name}")
    
    with tab3:
        metadata = item.get('metadata', {})
        
        if source_name == 'instagram':
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Likes:** {metadata.get('likes', 0)}")
                st.markdown(f"**Comments:** {metadata.get('comments_count', 0)}")
                st.markdown(f"**Content Type:** {metadata.get('content_type', 'post')}")
            with col2:
                st.markdown(f"**Username:** {metadata.get('username', 'N/A')}")
                st.markdown(f"**Media Type:** {metadata.get('media_type', 'text')}")
        
        elif source_name == 'claude':
            st.markdown(f"**Query Type:** {metadata.get('query_type', 'general')}")
            st.markdown(f"**Data Source:** {metadata.get('data_source', 'claude_analysis')}")
        
        else:
            for key, value in metadata.items():
                if value and key not in ['source_type', 'processing_time']:
                    st.markdown(f"**{key.title()}:** {value}")

def display_export_options(scraped_data: Dict[str, List[Dict]], comprehensive_analysis: Dict, location: str):
    """Display data export options"""
    if not scraped_data:
        return
    
    st.sidebar.subheader("📥 Export Options")
    
    # Prepare export data
    all_export_data = []
    for source, data in scraped_data.items():
        all_export_data.extend(data)
    
    if all_export_data:
        df_export = pd.DataFrame(all_export_data)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # CSV export
        csv_data = df_export.to_csv(index=False)
        st.sidebar.download_button(
            label="📄 Download CSV Data",
            data=csv_data,
            file_name=f"sentiment_analysis_{location}_{timestamp}.csv",
            mime="text/csv",
            help="Download raw data in CSV format"
        )
        
        # JSON export
        json_data = df_export.to_json(orient='records', date_format='iso')
        st.sidebar.download_button(
            label="📋 Download JSON Data",
            data=json_data,
            file_name=f"sentiment_analysis_{location}_{timestamp}.json",
            mime="application/json",
            help="Download structured data in JSON format"
        )
        
        # Analysis report export
        if comprehensive_analysis:
            analysis_json = json.dumps(comprehensive_analysis, indent=2, default=str)
            st.sidebar.download_button(
                label="🤖 Download AI Report",
                data=analysis_json,
                file_name=f"ai_analysis_report_{location}_{timestamp}.json",
                mime="application/json",
                help="Download comprehensive AI analysis report"
            )

def display_advanced_settings():
    """Display advanced analysis settings"""
    st.sidebar.subheader("⚙️ Analysis Settings")
    
    # Sentiment thresholds
    st.sidebar.markdown("**Sentiment Thresholds:**")
    positive_threshold = st.sidebar.slider("Positive Threshold", 0.0, 1.0, 0.1, 0.05)
    negative_threshold = st.sidebar.slider("Negative Threshold", -1.0, 0.0, -0.1, 0.05)
    
    # Analysis options
    st.sidebar.markdown("**Analysis Options:**")
    enable_detailed_analysis = st.sidebar.checkbox("Enable Detailed Analysis", value=True)
    include_historical_data = st.sidebar.checkbox("Include Historical Data", value=True)
    
    # Time filter
    st.sidebar.markdown("**Time Range:**")
    time_range = st.sidebar.selectbox(
        "Show data from:",
        ["Last hour", "Last 6 hours", "Last 24 hours", "Last week", "Last month", "All time"]
    )
    
    return {
        'positive_threshold': positive_threshold,
        'negative_threshold': negative_threshold,
        'enable_detailed_analysis': enable_detailed_analysis,
        'include_historical_data': include_historical_data,
        'time_range': time_range
    }

# ================================
# MAIN APPLICATION
# ================================

def main():
    """Main application entry point"""
    
    # Display header
    display_header()
    
    # Initialize components
    with st.spinner("🚀 Initializing system components..."):
        components = initialize_components()
    
    # Display system status and configuration
    display_system_status(components)
    display_configuration_guide(components)
    
    # Main application area
    location, scrape_button = display_location_selector()
    
    # Initialize session state
    if 'scraped_data' not in st.session_state:
        st.session_state.scraped_data = {}
    if 'comprehensive_analysis' not in st.session_state:
        st.session_state.comprehensive_analysis = {}
    if 'analysis_location' not in st.session_state:
        st.session_state.analysis_location = ""
    
    # Handle scrape button click
    if scrape_button:
        # Clear previous data if location changed
        if st.session_state.analysis_location != location:
            st.session_state.scraped_data = {}
            st.session_state.comprehensive_analysis = {}
        
        st.session_state.analysis_location = location
        
        st.header(f"🔍 Comprehensive Analysis for {location}")
        
        # Check if any scrapers are configured
        configured_scrapers = [(name, info) for name, info in components['scrapers'].items() if info['configured']]
        
        if not configured_scrapers:
            st.error("❌ No data sources configured. Please check the setup guide in the sidebar.")
            st.stop()
        
        # Progress tracking
        total_scrapers = len(configured_scrapers)
        overall_progress = st.progress(0, text="🚀 Starting comprehensive data collection...")
        
        # Scrape from each configured source
        scraped_data = {}
        
        for i, (source_name, scraper_info) in enumerate(configured_scrapers):
            try:
                st.subheader(f"{scraper_info['icon']} Analyzing {scraper_info['name']}")
                
                # Scrape data
                source_data = scrape_source_data(source_name, scraper_info, location, components)
                scraped_data[source_name] = source_data
                
                # Show results
                if source_data:
                    st.success(f"✅ {scraper_info['name']}: Found {len(source_data)} items")
                    
                    # Show sample for high-value sources
                    if source_name in ['instagram', 'claude'] and len(source_data) > 0:
                        sample = source_data[0]
                        with st.expander(f"📋 Sample {scraper_info['name']} insight"):
                            st.write(f"**Sentiment:** {sample['sentiment']} ({sample['score']:.2f})")
                            st.write(f"**Preview:** {sample['raw_text'][:200]}...")
                else:
                    st.warning(f"⚪ {scraper_info['name']}: No data found")
                
                # Update progress
                progress = (i + 1) / total_scrapers
                overall_progress.progress(progress, text=f"📊 Completed {i+1}/{total_scrapers} sources")
                
            except Exception as e:
                st.error(f"❌ {scraper_info['name']}: {str(e)}")
                logger.error(f"Error scraping {source_name}: {e}")
        
        # Store results
        st.session_state.scraped_data = scraped_data
        
        # Perform comprehensive analysis
        if scraped_data:
            overall_progress.progress(0.9, text="🤖 Performing AI analysis...")
            comprehensive_analysis = perform_comprehensive_analysis(scraped_data, location, components)
            st.session_state.comprehensive_analysis = comprehensive_analysis
        
        overall_progress.progress(1.0, text="🎉 Analysis completed!")
        time.sleep(1)
        st.rerun()
    
    # Display results if available
    if st.session_state.scraped_data:
        # Display comprehensive analysis
        if st.session_state.comprehensive_analysis:
            display_comprehensive_analysis(st.session_state.comprehensive_analysis)
        
        # Display overall dashboard
        display_overall_dashboard(st.session_state.scraped_data)
        
        # Display source-specific analysis
        st.header("🔍 Source-Specific Analysis")
        
        # Create tabs for each source
        available_sources = list(st.session_state.scraped_data.keys())
        if available_sources:
            source_tabs = st.tabs([
                f"{components['scrapers'][source]['icon']} {components['scrapers'][source]['name']}"
                for source in available_sources
            ])
            
            for i, source_name in enumerate(available_sources):
                with source_tabs[i]:
                    scraper_info = components['scrapers'][source_name]
                    data = st.session_state.scraped_data[source_name]
                    display_source_analysis(source_name, scraper_info, data)
    
    # Display historical data if no fresh scraping
    elif components['db_ops']:
        st.header("📊 Historical Data Analysis")
        
        try:
            sentiment_data = components['db_ops'].get_sentiment_by_location(location)
            
            if sentiment_data:
                st.info(f"📈 Showing historical data for {location}. Click 'Start Analysis' for fresh insights.")
                
                # Group by source and display
                df = pd.DataFrame(sentiment_data)
                
                for source in df['source'].unique():
                    source_data = df[df['source'] == source].to_dict('records')
                    
                    # Find scraper info
                    scraper_info = components['scrapers'].get(source, {
                        'icon': '📄',
                        'name': source.title(),
                        'configured': False
                    })
                    
                    with st.expander(f"{scraper_info['icon']} {scraper_info['name']} Historical Data ({len(source_data)} items)"):
                        display_source_analysis(source, scraper_info, source_data)
            else:
                st.info(f"📋 No historical data found for {location}. Click 'Start Analysis' to begin.")
        
        except Exception as e:
            st.error(f"Error loading historical data: {e}")
    
    # Sidebar features
    display_export_options(
        st.session_state.scraped_data, 
        st.session_state.comprehensive_analysis, 
        st.session_state.analysis_location
    )
    
    settings = display_advanced_settings()
    
    # Debug information
    if st.sidebar.checkbox("🔧 Show Debug Info"):
        st.sidebar.subheader("🔧 Debug Information")
        
        # System status
        st.sidebar.write("**System Status:**")
        st.sidebar.write(f"Database: {'✅' if components['db_ops'] else '❌'}")
        st.sidebar.write(f"Claude AI: {'✅' if components.get('claude_configured', False) else '❌'}")
        st.sidebar.write(f"Sentiment Analyzer: {'✅' if components['sentiment_analyzer'] else '❌'}")
        
        # Session data
        st.sidebar.write("**Session Data:**")
        st.sidebar.write(f"Active Location: {st.session_state.analysis_location}")
        st.sidebar.write(f"Data Sources: {list(st.session_state.scraped_data.keys())}")
        
        total_items = sum(len(data) for data in st.session_state.scraped_data.values())
        st.sidebar.write(f"Total Items: {total_items}")
        
        # Configuration status
        if components.get('config_validation'):
            st.sidebar.write("**Configuration:**")
            for component, status in components['config_validation'].items():
                st.sidebar.write(f"{component}: {'✅' if status else '❌'}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application error: {e}")
        logger.error(f"Application error: {e}")
        st.info("Please refresh the page and try again. Check the debug information for more details.")