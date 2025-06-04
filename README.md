# 🏠 Enhanced Real Estate Sentiment Analysis

AI-powered comprehensive sentiment analysis for Hyderabad real estate market with multi-source data aggregation and Claude AI intelligence.

## Features

**Multi-Source Data Collection**: Instagram posts and engagement, Reddit discussions, YouTube comments, Twitter posts, News articles, Claude AI market analysis

**Advanced AI Analysis**: Claude 3.5 Sonnet for sentiment analysis and real-time web search, comprehensive market intelligence and investment recommendations, automated risk assessment and opportunity identification

**Professional Dashboard**: Real-time sentiment tracking with interactive visualizations, source-specific analysis with engagement metrics, export capabilities for further analysis

**Instagram Integration**: Real-time Instagram data with likes, comments, and user engagement, hashtag-based property discovery, content type analysis (posts, comments, replies)

## Quick Start

Clone the repository and install dependencies:

```bash
git clone https://github.com/yourusername/real-estate-sentiment-analysis.git
cd real-estate-sentiment-analysis
pip install -r requirements.txt
```

Set up your environment variables by creating a `.env` file:

```env
CLAUDE_API_KEY=your_claude_api_key
INSTAGRAM_ACCESS_TOKEN=your_instagram_token
INSTAGRAM_USER_ID=your_instagram_user_id
REDDIT_CLIENT_ID=your_reddit_id
REDDIT_CLIENT_SECRET=your_reddit_secret
YOUTUBE_API_KEY=your_youtube_key
```

Run the application:

```bash
streamlit run ui/app.py
```

## API Configuration

**Claude AI** (Required): Get your API key from https://console.anthropic.com and set `CLAUDE_API_KEY` in your `.env` file. This enables both sentiment analysis and real-time web search capabilities.

**Instagram Graph API**: Create a Facebook Developer account, set up Instagram Basic Display app, and configure `INSTAGRAM_ACCESS_TOKEN` and `INSTAGRAM_USER_ID` for social media data collection.

**Reddit API**: Register at https://www.reddit.com/prefs/apps, create a script-type app, and set `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` for community discussions.

**YouTube Data API**: Enable YouTube Data API v3 in Google Cloud Console and set `YOUTUBE_API_KEY` for video comment analysis.

## Core Architecture

The application follows a modular architecture with distinct components for data collection, processing, and analysis. The scraper modules handle data collection from various sources, while the preprocessing components clean and prepare data for analysis. Claude AI serves as both the sentiment analysis engine and the web search provider, eliminating the need for external search APIs.

**Scrapers**: Individual modules for each data source (Instagram, Reddit, YouTube, Twitter, News, Claude AI) with standardized interfaces and error handling.

**Processing Pipeline**: Text cleaning and location extraction, Claude-powered sentiment analysis, database storage for historical tracking.

**Analysis Engine**: Real-time market context through Claude web search, comprehensive investment recommendations, risk assessment and opportunity identification.

## Project Structure

```
├── scrapers/                 # Data collection modules
│   ├── instagram_scraper.py  # Instagram Graph API integration
│   ├── reddit_scraper.py     # Reddit discussions
│   ├── youtube_scraper.py    # YouTube comments
│   ├── twitter_scraper.py    # Twitter posts
│   ├── news_scraper.py       # News articles
│   └── claude_scraper.py     # Claude AI market analysis
├── preprocessing/            # Data processing
│   ├── cleaner.py           # Text cleaning and preprocessing
│   ├── location_extractor.py # Location identification
│   └── claude_sentiment_analyzer.py # AI-powered analysis
├── database/                # Data persistence
│   ├── models.py           # Database schema
│   ├── operations.py       # Database operations
│   └── db.py              # Database connection
├── config/                 # Configuration management
│   └── config.py          # Settings and API keys
├── ui/                    # User interface
│   └── app.py            # Streamlit application
└── requirements.txt      # Python dependencies
```

## Usage Examples

**Location Analysis**: Select any Hyderabad locality from the dropdown or enter a custom location. The system will analyze sentiment across all configured data sources and provide comprehensive insights.

**Real-time Data**: Click "Start Analysis" to begin fresh data collection from Instagram, Reddit, YouTube, and other sources. The system processes data in real-time and provides immediate feedback.

**AI Insights**: Claude AI analyzes market context, provides investment recommendations, identifies risks and opportunities, and generates comprehensive reports with specific data points and trends.

**Export and Integration**: Download analysis results in CSV or JSON format, export AI reports for presentations, integrate historical data for trend analysis.

## System Requirements

Python 3.8 or higher is required. The application uses Streamlit for the web interface, pandas and plotly for data analysis and visualization, and the Anthropic library for Claude AI integration. Database operations use SQLAlchemy with SQLite for local storage.

## API Costs

Claude AI operates on a pay-per-use model with typical daily costs ranging from $1-5 for standard usage. Instagram Graph API provides a free tier with 200 requests per hour. Reddit and YouTube APIs are free with generous rate limits. The system is designed to be cost-effective while providing comprehensive analysis capabilities.

## Troubleshooting

**Claude API Issues**: Verify your API key is correct and has sufficient credits. Check internet connectivity and ensure the account is in good standing. The system provides fallback analysis if Claude is unavailable.

**Instagram API Problems**: Confirm your access token is valid and the Instagram Business Account is properly linked. Ensure your app has the necessary permissions and hasn't exceeded rate limits.

**No Data Found**: Try different location names or check if APIs are properly configured. Verify network connectivity and API key validity. The system provides guidance for missing configurations.

**Configuration Errors**: Use the built-in configuration guide in the sidebar to set up missing components. The application validates all configurations on startup and provides specific setup instructions.

## Contributing

This project welcomes contributions for new data sources, enhanced analysis capabilities, improved visualizations, and better error handling. Please ensure all API keys are properly secured and never committed to version control. Follow the existing code structure and include comprehensive error handling in new features.

## License

This project is licensed under the MIT License, allowing for both personal and commercial use with appropriate attribution.
