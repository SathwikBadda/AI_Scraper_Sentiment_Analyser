# scrapers/instagram_scraper.py
import requests
import json
from scrapers.base_scraper import BaseScraper
from config.config import Config
from typing import List, Dict
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class InstagramScraper(BaseScraper):
    def __init__(self):
        super().__init__("instagram")
        self.access_token = Config.INSTAGRAM_ACCESS_TOKEN
        self.base_url = "https://graph.instagram.com"
        self.business_discovery_url = f"{self.base_url}/v18.0"
        
    def is_configured(self) -> bool:
        """Check if Instagram API is properly configured"""
        return bool(self.access_token)
    
    def _search_hashtags(self, hashtag: str, limit: int = 50) -> List[Dict]:
        """Search posts by hashtag using Instagram Basic Display API"""
        results = []
        
        try:
            # Use hashtag search endpoint
            url = f"{self.business_discovery_url}/ig_hashtag_search"
            params = {
                'user_id': Config.INSTAGRAM_USER_ID,
                'q': hashtag,
                'access_token': self.access_token
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data and len(data['data']) > 0:
                    hashtag_id = data['data'][0]['id']
                    
                    # Get recent media for this hashtag
                    media_url = f"{self.business_discovery_url}/{hashtag_id}/recent_media"
                    media_params = {
                        'user_id': Config.INSTAGRAM_USER_ID,
                        'fields': 'id,media_type,media_url,permalink,caption,timestamp,like_count,comments_count',
                        'limit': limit,
                        'access_token': self.access_token
                    }
                    
                    media_response = requests.get(media_url, params=media_params, timeout=10)
                    if media_response.status_code == 200:
                        media_data = media_response.json()
                        
                        if 'data' in media_data:
                            for post in media_data['data']:
                                try:
                                    # Get comments for each post
                                    comments = self._get_post_comments(post['id'])
                                    
                                    # Process main post
                                    post_text = post.get('caption', '')
                                    if post_text:
                                        results.append({
                                            'text': post_text,
                                            'url': post.get('permalink', ''),
                                            'timestamp': post.get('timestamp', datetime.now().isoformat()),
                                            'media_type': post.get('media_type', 'unknown'),
                                            'likes': post.get('like_count', 0),
                                            'comments_count': post.get('comments_count', 0),
                                            'post_id': post.get('id', ''),
                                            'content_type': 'post'
                                        })
                                    
                                    # Add comments
                                    results.extend(comments)
                                    
                                except Exception as e:
                                    logger.warning(f"Error processing Instagram post: {e}")
                                    continue
            
        except Exception as e:
            logger.error(f"Error searching Instagram hashtags: {e}")
        
        return results
    
    def _get_post_comments(self, post_id: str, limit: int = 20) -> List[Dict]:
        """Get comments for a specific post"""
        comments = []
        
        try:
            url = f"{self.business_discovery_url}/{post_id}/comments"
            params = {
                'fields': 'id,text,timestamp,username,like_count,replies',
                'limit': limit,
                'access_token': self.access_token
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data:
                    for comment in data['data']:
                        try:
                            comment_text = comment.get('text', '')
                            if comment_text and len(comment_text.strip()) > 10:
                                comments.append({
                                    'text': comment_text,
                                    'url': f"https://instagram.com/p/{post_id}",
                                    'timestamp': comment.get('timestamp', datetime.now().isoformat()),
                                    'username': comment.get('username', 'anonymous'),
                                    'likes': comment.get('like_count', 0),
                                    'comment_id': comment.get('id', ''),
                                    'content_type': 'comment'
                                })
                                
                                # Get replies if available
                                if 'replies' in comment:
                                    replies = self._get_comment_replies(comment['id'])
                                    comments.extend(replies)
                                    
                        except Exception as e:
                            logger.warning(f"Error processing Instagram comment: {e}")
                            continue
        
        except Exception as e:
            logger.warning(f"Error fetching Instagram comments: {e}")
        
        return comments
    
    def _get_comment_replies(self, comment_id: str, limit: int = 10) -> List[Dict]:
        """Get replies to a specific comment"""
        replies = []
        
        try:
            url = f"{self.business_discovery_url}/{comment_id}/replies"
            params = {
                'fields': 'id,text,timestamp,username,like_count',
                'limit': limit,
                'access_token': self.access_token
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data:
                    for reply in data['data']:
                        try:
                            reply_text = reply.get('text', '')
                            if reply_text and len(reply_text.strip()) > 5:
                                replies.append({
                                    'text': reply_text,
                                    'url': f"https://instagram.com/p/{comment_id}",
                                    'timestamp': reply.get('timestamp', datetime.now().isoformat()),
                                    'username': reply.get('username', 'anonymous'),
                                    'likes': reply.get('like_count', 0),
                                    'reply_id': reply.get('id', ''),
                                    'content_type': 'reply'
                                })
                        except Exception as e:
                            logger.warning(f"Error processing Instagram reply: {e}")
                            continue
        
        except Exception as e:
            logger.warning(f"Error fetching Instagram replies: {e}")
        
        return replies
    
    def _search_location_posts(self, location: str, limit: int = 30) -> List[Dict]:
        """Search posts by location using business discovery"""
        results = []
        
        try:
            # Search for location-specific hashtags
            location_hashtags = [
                f"{location.replace(' ', '').lower()}realestate",
                f"{location.replace(' ', '').lower()}property",
                f"{location.replace(' ', '').lower()}apartments",
                f"{location.replace(' ', '').lower()}flats",
                f"{location.replace(' ', '').lower()}homes",
                f"hyderabad{location.replace(' ', '').lower()}",
                f"{location.replace(' ', '').lower()}investment"
            ]
            
            for hashtag in location_hashtags:
                hashtag_results = self._search_hashtags(hashtag, limit // len(location_hashtags))
                results.extend(hashtag_results)
                
                if len(results) >= limit:
                    break
            
        except Exception as e:
            logger.error(f"Error searching Instagram location posts: {e}")
        
        return results[:limit]
    
    def _get_user_posts(self, username: str, limit: int = 20) -> List[Dict]:
        """Get posts from a specific user (for real estate accounts)"""
        results = []
        
        try:
            # First get user ID
            url = f"{self.business_discovery_url}/business_discovery"
            params = {
                'user_id': Config.INSTAGRAM_USER_ID,
                'username': username,
                'fields': 'business_discovery{id,username,media{id,caption,permalink,timestamp,like_count,comments_count,media_type}}',
                'access_token': self.access_token
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if 'business_discovery' in data and 'media' in data['business_discovery']:
                    media_data = data['business_discovery']['media']['data']
                    
                    for post in media_data[:limit]:
                        try:
                            post_text = post.get('caption', '')
                            if post_text:
                                results.append({
                                    'text': post_text,
                                    'url': post.get('permalink', ''),
                                    'timestamp': post.get('timestamp', datetime.now().isoformat()),
                                    'media_type': post.get('media_type', 'unknown'),
                                    'likes': post.get('like_count', 0),
                                    'comments_count': post.get('comments_count', 0),
                                    'username': username,
                                    'post_id': post.get('id', ''),
                                    'content_type': 'user_post'
                                })
                        except Exception as e:
                            logger.warning(f"Error processing user post: {e}")
                            continue
        
        except Exception as e:
            logger.error(f"Error fetching user posts for {username}: {e}")
        
        return results
    
    def scrape(self, query: str, limit: int = 50) -> List[Dict]:
        """Main scraping method for Instagram real estate content"""
        if not self.is_configured():
            logger.warning("Instagram API not configured")
            return []
        
        results = []
        
        try:
            logger.info(f"Scraping Instagram for location: {query}")
            
            # 1. Search location-based hashtags and posts
            location_posts = self._search_location_posts(query, limit // 3)
            results.extend(location_posts)
            
            # 2. Search general real estate hashtags with location filter
            real_estate_hashtags = [
                "hyderabadrealstate",
                "hyderabadproperty", 
                "realestatehyderabad",
                "propertyinhyderabad",
                "hyderabadflats",
                "hyderabadapartments",
                "hyderabadhomes",
                "hyderabadinvestment"
            ]
            
            for hashtag in real_estate_hashtags[:3]:  # Limit to avoid rate limits
                hashtag_results = self._search_hashtags(hashtag, limit // 6)
                # Filter results that mention the specific location
                filtered_results = [
                    result for result in hashtag_results 
                    if query.lower() in result['text'].lower()
                ]
                results.extend(filtered_results)
            
            # 3. Get posts from known real estate accounts
            real_estate_accounts = [
                "hyderabadrealestate",
                "propertyinhyderabad", 
                "hyderabadproperties",
                "realestatehyderabad",
                "hyderabadflats"
            ]
            
            for account in real_estate_accounts[:2]:  # Limit to avoid rate limits
                try:
                    user_posts = self._get_user_posts(account, limit // 10)
                    # Filter by location mention
                    filtered_posts = [
                        post for post in user_posts 
                        if query.lower() in post['text'].lower()
                    ]
                    results.extend(filtered_posts)
                except Exception as e:
                    logger.warning(f"Error fetching posts from {account}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error scraping Instagram: {e}")
        
        # Remove duplicates based on text content
        seen_texts = set()
        unique_results = []
        for result in results:
            text_key = result['text'][:100].lower().strip()
            if text_key not in seen_texts and len(result['text'].strip()) > 20:
                seen_texts.add(text_key)
                unique_results.append(result)
        
        logger.info(f"Scraped {len(unique_results)} unique Instagram posts/comments for query: {query}")
        return unique_results[:limit]