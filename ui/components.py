import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from typing import Dict, List, Any
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DashboardComponents:
    """Reusable UI components for the sentiment dashboard"""
    
    @staticmethod
    def render_header():
        """Render the main dashboard header"""
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
    
    @staticmethod
    def render_metrics_cards(summary: Dict[str, Any]):
        """Render metric cards with sentiment summary"""
        if not summary:
            st.warning("No data available for metrics")
            return
        
        sentiment_dist = summary.get('sentiment_distribution', {})
        total_mentions = summary.get('total_mentions', 0)
        
        # Calculate percentages
        positive_count = sentiment_dist.get('Positive', 0)
        negative_count = sentiment_dist.get('Negative', 0)
        neutral_count = sentiment_dist.get('Neutral', 0)
        
        positive_pct = (positive_count / total_mentions * 100) if total_mentions > 0 else 0
        negative_pct = (negative_count / total_mentions * 100) if total_mentions > 0 else 0
        neutral_pct = (neutral_count / total_mentions * 100) if total_mentions > 0 else 0
        
        # Calculate sentiment score
        sentiment_score = ((positive_count - negative_count) / total_mentions) if total_mentions > 0 else 0
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                label="📊 Total Mentions",
                value=total_mentions,
                help="Total number of mentions found"
            )
        
        with col2:
            st.metric(
                label="✅ Positive",
                value=f"{positive_count} ({positive_pct:.1f}%)",
                delta=f"{positive_pct:.1f}%",
                delta_color="normal"
            )
        
        with col3:
            st.metric(
                label="❌ Negative", 
                value=f"{negative_count} ({negative_pct:.1f}%)",
                delta=f"{negative_pct:.1f}%",
                delta_color="inverse"
            )
        
        with col4:
            st.metric(
                label="⚪ Neutral",
                value=f"{neutral_count} ({neutral_pct:.1f}%)",
                help="Neutral sentiment mentions"
            )
        
        with col5:
            # Sentiment score indicator
            score_color = "normal" if sentiment_score > 0 else "inverse" if sentiment_score < 0 else "off"
            st.metric(
                label="📈 Sentiment Score",
                value=f"{sentiment_score:.2f}",
                delta=f"{'Positive' if sentiment_score > 0 else 'Negative' if sentiment_score < 0 else 'Neutral'}",
                delta_color=score_color,
                help="Overall sentiment score (-1 to +1)"
            )
    
    @staticmethod
    def render_sentiment_pie_chart(sentiment_data: Dict[str, int]):
        """Render sentiment distribution pie chart"""
        if not sentiment_data:
            st.warning("No sentiment data available")
            return
        
        # Prepare data
        labels = list(sentiment_data.keys())
        values = list(sentiment_data.values())
        
        # Color mapping
        colors = {
            'Positive': '#00CC96',
            'Negative': '#EF553B',
            'Neutral': '#636EFA'
        }
        
        color_list = [colors.get(label, '#636EFA') for label in labels]
        
        # Create pie chart
        fig = go.Figure(data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                marker_colors=color_list,
                textinfo='label+percent+value',
                textfont_size=12,
                hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title={
                'text': "Sentiment Distribution",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            showlegend=True,
            height=400,
            margin=dict(t=50, b=50, l=50, r=50)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def render_source_distribution_chart(source_data: Dict[str, int]):
        """Render source distribution bar chart"""
        if not source_data:
            st.warning("No source data available")
            return
        
        # Prepare data
        sources = list(source_data.keys())
        counts = list(source_data.values())
        
        # Create bar chart
        fig = go.Figure(data=[
            go.Bar(
                x=sources,
                y=counts,
                marker_color='#1f77b4',
                text=counts,
                textposition='auto',
                hovertemplate='<b>%{x}</b><br>Mentions: %{y}<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title={
                'text': "Mentions by Source",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            xaxis_title="Data Source",
            yaxis_title="Number of Mentions",
            height=400,
            margin=dict(t=50, b=50, l=50, r=50)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def render_sentiment_timeline(df: pd.DataFrame):
        """Render sentiment over time chart"""
        if df.empty:
            st.warning("No data available for timeline")
            return
        
        try:
            # Prepare timeline data
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp'].dt.date
            
            # Group by date and sentiment
            timeline_data = df.groupby(['date', 'sentiment']).size().reset_index(name='count')
            
            if timeline_data.empty:
                st.warning("No timeline data available")
                return
            
            # Create line chart
            fig = px.line(
                timeline_data,
                x='date',
                y='count',
                color='sentiment',
                color_discrete_map={
                    'Positive': '#00CC96',
                    'Negative': '#EF553B',
                    'Neutral': '#636EFA'
                },
                title="Sentiment Trends Over Time",
                markers=True
            )
            
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Number of Mentions",
                height=400,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            logger.error(f"Error rendering timeline: {e}")
            st.error("Error displaying timeline chart")
    
    @staticmethod
    def render_word_cloud(text_data: List[str], title: str = "Key Topics"):
        """Render word cloud from text data"""
        if not text_data:
            st.warning("No text data available for word cloud")
            return
        
        try:
            # Combine all text
            combined_text = ' '.join([text for text in text_data if text and text.strip()])
            
            if not combined_text.strip():
                st.warning("No valid text for word cloud")
                return
            
            # Generate word cloud
            wordcloud = WordCloud(
                width=800,
                height=400,
                background_color='white',
                colormap='viridis',
                max_words=100,
                relative_scaling=0.5,
                min_font_size=10
            ).generate(combined_text)
            
            # Display word cloud
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
            
            st.pyplot(fig)
            plt.close()
            
        except Exception as e:
            logger.error(f"Error generating word cloud: {e}")
            st.error("Error generating word cloud")
    
    @staticmethod
    def render_data_table(df: pd.DataFrame, title: str = "Recent Mentions"):
        """Render data table with recent mentions"""
        if df.empty:
            st.warning("No data available for table")
            return
        
        try:
            # Prepare display dataframe
            display_df = df.copy()
            
            # Format timestamp
            display_df['timestamp'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
            
            # Truncate long text
            if 'raw_text' in display_df.columns:
                display_df['text_preview'] = display_df['raw_text'].str[:100] + '...'
                display_df = display_df.drop('raw_text', axis=1)
            
            # Reorder columns
            column_order = ['timestamp', 'source', 'location', 'sentiment', 'score', 'reason', 'text_preview']
            display_columns = [col for col in column_order if col in display_df.columns]
            display_df = display_df[display_columns]
            
            # Apply styling based on sentiment
            def highlight_sentiment(row):
                if row['sentiment'] == 'Positive':
                    return ['background-color: #d4edda'] * len(row)
                elif row['sentiment'] == 'Negative':
                    return ['background-color: #f8d7da'] * len(row)
                else:
                    return ['background-color: #e2e3e5'] * len(row)
            
            styled_df = display_df.style.apply(highlight_sentiment, axis=1)
            
            st.subheader(title)
            st.dataframe(styled_df, use_container_width=True, height=400)
            
        except Exception as e:
            logger.error(f"Error rendering data table: {e}")
            st.error("Error displaying data table")
    
    @staticmethod
    def render_sidebar_controls():
        """Render sidebar controls and configuration"""
        st.sidebar.header("⚙️ Configuration")
        
        # Refresh settings
        st.sidebar.subheader("Data Refresh")
        refresh_interval = st.sidebar.selectbox(
            "Auto-refresh interval:",
            options=[0, 5, 10, 15, 30],
            format_func=lambda x: "Manual" if x == 0 else f"{x} minutes",
            help="Set automatic data refresh interval"
        )
        
        # Data source filters
        st.sidebar.subheader("Data Sources")
        source_filters = {
            'news': st.sidebar.checkbox("📰 News", value=True),
            'youtube': st.sidebar.checkbox("🎥 YouTube", value=True),
            'reddit': st.sidebar.checkbox("🔗 Reddit", value=True),
            'twitter': st.sidebar.checkbox("🐦 Twitter", value=True),
            'perplexity': st.sidebar.checkbox("🤖 Perplexity", value=True)
        }
        
        # Sentiment filters
        st.sidebar.subheader("Sentiment Filters")
        sentiment_filters = {
            'positive': st.sidebar.checkbox("✅ Positive", value=True),
            'negative': st.sidebar.checkbox("❌ Negative", value=True),
            'neutral': st.sidebar.checkbox("⚪ Neutral", value=True)
        }
        
        # Date range filter
        st.sidebar.subheader("Date Range")
        date_range = st.sidebar.date_input(
            "Select date range:",
            value=[datetime.now().date() - timedelta(days=7), datetime.now().date()],
            help="Filter data by date range"
        )
        
        return {
            'refresh_interval': refresh_interval,
            'source_filters': source_filters,
            'sentiment_filters': sentiment_filters,
            'date_range': date_range
        }
    
    @staticmethod
    def render_api_status(api_status: Dict[str, bool]):
        """Render API configuration status"""
        st.sidebar.subheader("🔗 API Status")
        
        for api_name, is_configured in api_status.items():
            if is_configured:
                st.sidebar.success(f"✅ {api_name}")
            else:
                st.sidebar.error(f"❌ {api_name}")
                
        # Configuration help
        with st.sidebar.expander("🔧 API Setup Help"):
            st.markdown("""
            **Required APIs:**
            - **YouTube**: Google Cloud Console → YouTube Data API v3
            - **Reddit**: Reddit Apps → Create Script App
            - **Perplexity**: Perplexity AI → API Access
            
            **Optional APIs:**
            - **Twitter**: Uses snscrape (no API key needed)
            - **News**: Uses RSS feeds (no API key needed)
            
            Add your API keys to the `.env` file.
            """)
    
    @staticmethod
    def render_export_options(df: pd.DataFrame):
        """Render data export options"""
        if df.empty:
            return
        
        st.sidebar.subheader("📥 Export Data")
        
        # CSV export
        csv_data = df.to_csv(index=False)
        st.sidebar.download_button(
            label="📄 Download CSV",
            data=csv_data,
            file_name=f"sentiment_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
        # JSON export
        json_data = df.to_json(orient='records', date_format='iso')
        st.sidebar.download_button(
            label="📋 Download JSON",
            data=json_data,
            file_name=f"sentiment_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )