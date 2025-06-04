#!/usr/bin/env python3
"""
Real Estate Sentiment Analysis - Main Application
Fixed version with proper imports
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

# Configure page
st.set_page_config(
    page_title="Real Estate Sentiment Analysis",
    page_icon="🏠",
    layout="wide"
)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_components():
    """Initialize all system components with error handling"""
    components = {}
    
    try:
        from database.operations import DatabaseOperations
        components['db_ops'] = DatabaseOperations()
        st.sidebar.success("✅ Database initialized")
    except Exception as e:
        st.sidebar.error(f"❌ Database error: {e}")
        components['db_ops'] = None
    
    try:
        from config.config import Config
        components['config'] = Config
        st.sidebar.success("✅ Configuration loaded")
    except Exception as e:
        st.sidebar.error(f"❌ Config error: {e}")
        components['config'] = None
    
    # Initialize scrapers with error handling
    components['scrapers'] = {}
    
    scraper_modules = [
        ('news', 'scrapers.news_scraper', 'NewsScraper'),
        ('youtube', 'scrapers.youtube_scraper', 'YouTubeScraper'),
        ('reddit', 'scrapers.reddit_scraper', 'RedditScraper'),
        ('twitter', 'scrapers.twitter_scraper', 'TwitterScraper'),
    ]
    
    for name, module_path, class_name in scraper_modules:
        try:
            module = __import__(module_path, fromlist=[class_name])
            scraper_class = getattr(module, class_name)
            components['scrapers'][name] = scraper_class()
            st.sidebar.success(f"✅ {name.title()} scraper loaded")
        except Exception as e:
            st.sidebar.warning(f"⚠️ {name.title()} scraper: {e}")
            components['scrapers'][name] = None
    
    # Initialize preprocessing components
    try:
        from preprocessing.cleaner import TextCleaner
        from preprocessing.location_extractor import LocationExtractor
        from preprocessing.claude_sentiment_analyzer import SentimentAnalyzer
        
        components['cleaner'] = TextCleaner()
        components['location_extractor'] = LocationExtractor()
        components['sentiment_analyzer'] = SentimentAnalyzer()
        st.sidebar.success("✅ Preprocessing components loaded")
        
    except Exception as e:
        st.sidebar.error(f"❌ Preprocessing error: {e}")
        components['cleaner'] = None
        components['location_extractor'] = None
        components['sentiment_analyzer'] = None
    
    return components

def main():
    """Main application"""
    
    # Header
    st.markdown("""
    <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
                padding: 2rem; border-radius: 10px; margin-bottom: 2rem;">
        <h1 style="color: white; text-align: center; margin: 0;">
            🏠 Real Estate Sentiment Analysis
        </h1>
        <p style="color: white; text-align: center; margin: 0.5rem 0 0 0;">
            Real-time sentiment tracking for Hyderabad property market
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize components
    with st.spinner("Initializing system components..."):
        components = initialize_components()
    
    # Sidebar configuration
    st.sidebar.header("📍 Location Selection")
    
    # Default locations
    hyderabad_localities = [
        'Kondapur', 'Gachibowli', 'Madhapur', 'Hitech City', 'Banjara Hills',
        'Jubilee Hills', 'Kukatpally', 'Miyapur', 'Begumpet', 'Secunderabad',
        'Ameerpet', 'Somajiguda', 'Abids', 'Charminar', 'Dilsukhnagar',
        'Uppal', 'Kompally', 'Bachupally', 'Nizampet', 'Manikonda'
    ]
    
    location = st.sidebar.selectbox(
        "Choose a location:",
        options=hyderabad_localities,
        index=0
    )
    
    # Custom location input
    custom_location = st.sidebar.text_input("Or enter custom location:")
    if custom_location:
        location = custom_location
    
    st.sidebar.markdown("---")
    
    # System status
    st.sidebar.header("🔧 System Status")
    
    # Mock refresh functionality for now
    if st.sidebar.button("🔄 Refresh Data", type="primary"):
        with st.spinner(f"Fetching data for {location}..."):
            # Simulate data fetching
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.01)
                progress_bar.progress(i + 1)
            
            st.success(f"✅ Data refreshed for {location}!")
            
            # Show mock results
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Mentions", "156", "12")
            with col2:
                st.metric("Positive", "89 (57%)", "5.2%")
            with col3:
                st.metric("Negative", "34 (22%)", "-2.1%")
            with col4:
                st.metric("Neutral", "33 (21%)", "1.2%")
            
            # Mock pie chart
            st.subheader("Sentiment Distribution")
            fig = px.pie(
                values=[89, 34, 33],
                names=['Positive', 'Negative', 'Neutral'],
                color_discrete_map={'Positive': '#00CC96', 'Negative': '#EF553B', 'Neutral': '#636EFA'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Mock data table
            st.subheader("Recent Mentions")
            mock_data = pd.DataFrame({
                'Source': ['News', 'Reddit', 'YouTube', 'Twitter'],
                'Sentiment': ['Positive', 'Neutral', 'Positive', 'Negative'],
                'Text': [
                    f'Great infrastructure development in {location}...',
                    f'Looking for properties in {location} area...',
                    f'Amazing connectivity in {location} IT hub...',
                    f'Traffic issues reported in {location}...'
                ],
                'Score': [0.65, 0.02, 0.78, -0.45],
                'Timestamp': ['2024-01-15 10:30', '2024-01-15 09:15', '2024-01-15 08:45', '2024-01-15 07:20']
            })
            st.dataframe(mock_data, use_container_width=True)
    
    # Information section
    with st.expander("ℹ️ How it works"):
        st.markdown("""
        This system analyzes real estate sentiment for Hyderabad locations by:
        
        1. **Data Collection**: Scrapes data from multiple sources (News, YouTube, Reddit, Twitter)
        2. **Text Processing**: Cleans and preprocesses the collected text data
        3. **Location Extraction**: Identifies specific Hyderabad localities mentioned
        4. **Sentiment Analysis**: Uses VADER and transformer models to classify sentiment
        5. **Visualization**: Presents insights through interactive charts and summaries
        
        **Note**: This is a demo version. Configure your API keys to enable full functionality.
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("Made with ❤️ for Hyderabad Real Estate Analysis")

if __name__ == "__main__":
    main()
