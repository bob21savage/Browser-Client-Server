import re
import json
import random
import asyncio
import logging
import sqlite3
import aiohttp
import html2text
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin, quote, urlparse
from typing import List, Dict, Any
from flask_socketio import emit
import os
import requests

# Initialize the database connection
db_connection = sqlite3.connect('instance/advanced_scraper.db')

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AdvancedContentScraper:
    def __init__(self) -> None:
        """Initialize the content scraper with SearX and enhanced media support."""
        # List of common user agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15'
        ]
        
        # Initialize HTML converter
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        
        # Initialize cache
        self._cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache')
        os.makedirs(self._cache_dir, exist_ok=True)
        self._cache_durations = {
            'web': 7200,      # 2 hours for web results
            'images': 3600,   # 1 hour for images
            'news': 1800,     # 30 minutes for news
            'videos': 3600,   # 1 hour for videos
            'audio': 3600     # 1 hour for audio
        }
        self._default_cache_duration = 3600
        
        # SearX configuration
        self.searx_instances = [
            'https://searx.be',
            'https://search.ononoki.org',
            'https://searx.tiekoetter.com',
            'https://search.bus-hit.me',
            'https://search.leptons.xyz'
        ]
        
        # Proxy configuration
        self._proxy_list = self._load_proxies()
        self._proxy_failures = {}
        
        # Session management
        self._session = None
        
        # Rate limiting
        self._last_request_time = {}
        self._min_delay = {
            'searx': 1.0,  # 1 second between requests
            'general': 0.5  # 0.5 seconds for other requests
        }
        self._max_retries = 3
        self._max_requests_per_minute = 20  # SearX allows more requests
        
        self.spec = {
            'icon': 'cinema.ico',  # Add the icon file here
            'name': 'scrape_upgrade',
            'version': '1.0',
            'description': 'A scraper for video search',
        }
        
    async def search(self, query: str, content_types: List[str] = None) -> Dict[str, List[Dict]]:
        """Execute a search across multiple content types concurrently."""
        # ... (rest of the search method)

class VideoSearchCrawler:
    def __init__(self, topic: str):
        self.main_topic = topic
        self.search_results = []
        self.seen_links = set()
        self.search_completed = False
        self.session = requests.Session()
        self.max_results = 1000  # Increased max results
        self.min_results = 50
        self.max_pages = 10
        self.delay = 3  # Increased delay between requests
        self.last_count = 0  # Initialize a variable to track the last count of results
        
        # Initialize headers
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15'
        ]
        self.headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # List of search engines to query
        self.search_engines = [
            'https://search.aol.com/aol/search?q=',
            'https://www.google.com/search?q=',
            'https://www.bing.com/search?q=',
            'https://search.yahoo.com/search?p=',
            'https://duckduckgo.com/?q=',
            'https://www.baidu.com/s?wd=',
            'https://www.yandex.com/search/?text=',
            'https://www.ask.com/web?q=',
            'https://www.aol.com/search?q=',
            'https://www.wolframalpha.com/input/?i=',
            'https://www.startpage.com/do/search?q=',
            'https://www.qwant.com/?q=',
            'https://www.searchencrypt.com/search?q=',
            'https://www.exalead.com/search/',
            'https://www.kiddle.co/',
            'https://www.yippy.com/search?query=',
            'https://www.dogpile.com/search/web?q=',
            'https://www.metacrawler.com/search/web?q=',
            'https://www.gigablast.com/search?q=',
            'https://www.lycos.com/search?q=',
            'https://www.webcrawler.com/search/web?q=',
            'https://www.info.com/search?q=',
            'https://www.teoma.com/search?q=',
            'https://www.bing.com/videos/search?q=',
            'https://www.vimeo.com/search?q=',
            'https://www.dailymotion.com/search?q=',
            'https://www.twitch.tv/search?term=',
            'https://www.tiktok.com/search?q=',
            'https://www.search.com/search?q=',
            'https://www.goo.gl/search?q=',
            'https://www.filehorse.com/search?q=',
            'https://www.searchenginewatch.com/?s=',
            'https://www.searchtempest.com/search?q=',
            'https://www.explore.com/search?q=',
            'https://www.searchresults.com/search?q=',
            'https://www.qwant.com/?q=',
            'https://www.find.com/search?q=',
            'https://www.searchenginejournal.com/search?q=',
            'https://vimeo.com/search?q=',
            'https://www.facebook.com/watch/search/?q=',
            'https://www.veoh.com/search/videos?q=',
            'https://www.metacafe.com/search/videos?q=',
            'https://www.bitchute.com/search/?query=',
            'https://rumble.com/search/?query=',
            'https://soundcloud.com/search?q=',
            'https://open.spotify.com/search?q=',
            'https://tidal.com/search?q=',
            'https://www.amazon.com/music/search?q=',
            'https://www.pandora.com/search?q=',
            'https://www.iheart.com/search?q=',
            'https://www.mixcloud.com/search?q=',
            'https://www.last.fm/search?q=',
            'https://www.beatport.com/search?q=',
            'https://www.buzzfeed.com/search?q=',
            'https://www.huffpost.com/search?q=',
            'https://www.cnn.com/search?q=',
            'https://www.vice.com/search?q=',
        ]
        
    async def collect_results(self):
        logger.info(f"Starting search for: {self.main_topic}")
        for engine in self.search_engines:
            search_url = f'{engine}{self.main_topic}'
            logger.info(f"Searching URL: {search_url}")
            try:
                html_content = await self.fetch_search_results(search_url)
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection error with {engine}: {e}. Trying next engine.")
                continue  # Skip to the next engine if there's a connection error
            if html_content:
                # Extract URLs from the HTML content
                results = self.extract_page_urls(html_content, search_url)
                
                # Log the extracted URLs
                if results:
                    logger.info(f"Extracted URLs from {search_url}:")
                    for result in results:
                        logger.info(f"- {result['link']} (Title: {result['title']})")  # Assuming your results include a title
                
                # Add extracted results to the main results list
                self.search_results.extend(results)
                logger.info(f"Total results after {engine}: {len(self.search_results)}")
            
            await asyncio.sleep(3)  # Increased delay between requests
        self.search_completed = True

    async def fetch_search_results(self, url: str):
        try:
            logger.info(f"Making GET request to: {url}")
            self.headers['User-Agent'] = random.choice(self.user_agents)
            response = self.session.get(url, headers=self.headers, timeout=10)  # 10 seconds timeout
            response.raise_for_status()  # Raises an error for HTTP error responses
            return response.text
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                logger.error(f"404 Not Found for URL: {url}")
                return []  # Skip this URL and return empty results
            else:
                logger.error(f"HTTP error occurred: {e}")
                return []  # Skip other errors as well

    def extract_page_urls(self, html_content: str, base_url: str):
        logger.info(f"Extracting URLs from HTML content.")
        soup = BeautifulSoup(html_content, 'html.parser')
        results = []
    
        # Extract URLs
        for link in soup.find_all('a'):
            href = link.get('href')
            title = link.get_text(strip=True)
    
            # Convert relative URLs to absolute URLs
            if href:
                full_url = urljoin(base_url, href)  # This will handle both relative and absolute URLs
                if title:
                    results.append({
                        'link': full_url,
                        'title': title,
                    })
                    logger.info(f"Extracted URL: {full_url} (Title: {title})")
                    if full_url not in self.search_results:
                        self.search_results.append({'link': full_url, 'title': title})
                        new_results = len(self.search_results) - self.last_count
                        self.last_count = len(self.search_results)
                        logger.info(f"Progress - Total Results: {self.last_count}, New Results: {new_results}, Last Count: {self.last_count - new_results}")
    
        logger.info(f"Found {len(results)} results.")
        return results

class VideoSearchCrawlerOriginal:
    def __init__(self, topic):
        # Initialize main topic, search results, and seen links
        self.main_topic = topic
        self.search_results = []
        self.seen_links = set()

        # Initialize HTML converter
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        
        # Initialize headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }


    async def collect_results(self):
        """Collect video results from multiple sources"""
        try:
            logger.info(f"Starting search for: {self.main_topic}")
            all_results = []
            
            # Create tasks for all search engines
            tasks = [
                self._search_youtube(self.main_topic),
                self._search_youtube_mobile(self.main_topic),
                self._search_bing_videos(self.main_topic),
                self._search_bing_videos_uk(self.main_topic)
            ]
            
            # Run all searches in parallel
            results = await asyncio.gather(*tasks)
            
            # Combine results
            for engine_results in results:
                if engine_results:
                    all_results.extend(engine_results)
                    logger.info(f"Found {len(engine_results)} results from {engine_results[0]['platform'] if engine_results else 'Unknown'}")
            
            # Shuffle results to mix platforms
            random.shuffle(all_results)
            return all_results
            
        except Exception as e:
            logger.error(f"Error in collect_results: {str(e)}")
            raise

    async def _search_youtube(self, query: str) -> List[Dict]:
        """Search for videos on YouTube."""
        results = []
        try:
            # Try different sorting options to get more results
            sort_params = ['', '&sp=CAI%253D', '&sp=CAM%253D']  # Default, Date, Rating
            
            for sort_param in sort_params:
                if len(results) >= 75:  
                    break
                    
                # YouTube search URL with sort parameter
                search_url = f"https://www.youtube.com/results?search_query={quote(query)}{sort_param}"
                logger.info(f"Constructed search URL: {search_url}")
                logger.info(f"Searching YouTube: {search_url}")
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(search_url, headers=self.headers) as response:
                        if response.status == 200:
                            html = await response.text()
                            logger.debug(f"HTML Response: {html}")  # <--- Added logging for HTML response
                            
                            # Extract video IDs using regex
                            video_ids = re.findall(r'"videoId":"([^"]+)"', html)
                            video_titles = re.findall(r'"title":{"runs":\[{"text":"([^"]+)"}]}', html)
                            video_durations = re.findall(r'"simpleText":"([0-9:]+)"', html)
                            video_views = re.findall(r'"viewCountText":{"simpleText":"([^"]+)"}', html)
                            
                            # Process unique video IDs
                            seen_ids = set()
                            for i, video_id in enumerate(video_ids):
                                if video_id in seen_ids or len(results) >= 75:  
                                    continue
                                    
                                seen_ids.add(video_id)
                                title = video_titles[i] if i < len(video_titles) else "Untitled Video"
                                duration = video_durations[i] if i < len(video_durations) else "Unknown"
                                views = video_views[i] if i < len(video_views) else "Unknown views"
                                
                                video_url = f"https://www.youtube.com/watch?v={video_id}"
                                thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
                                
                                results.append({
                                    'title': title,
                                    'url': video_url,
                                    'thumbnail': thumbnail_url,
                                    'duration': duration,
                                    'views': views,
                                    'platform': 'YouTube',
                                    'description': f"Watch this video on YouTube: {title}",
                                    'source': 'YouTube'
                                })
                                
        except Exception as e:
            logger.error(f"Error searching YouTube: {str(e)}")
        
        return results[:75]  

    async def _search_youtube_mobile(self, query: str) -> List[Dict]:
        """Search for videos on YouTube mobile site"""
        results = []
        try:
            # Search multiple pages
            for page in range(1, 4):  # Get up to 3 pages of results
                if len(results) >= 75:
                    break
                
                search_url = f"https://m.youtube.com/results?search_query={quote(query)}&page={page}"
                logger.info(f"Constructed search URL: {search_url}")
                logger.info(f"Searching YouTube Mobile page {page}: {search_url}")
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(search_url, headers=self.headers) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Find video elements
                            video_elements = soup.find_all('div', class_='compact-media-item')
                            logger.info(f"Found {len(video_elements)} video elements on YouTube Mobile page {page}")
                            
                            for element in video_elements:
                                try:
                                    if len(results) >= 75:
                                        break
                                    
                                    # Get video ID and title
                                    link = element.find('a', href=True)
                                    if not link:
                                        continue
                                        
                                    href = link.get('href', '')
                                    if not href or '/watch?v=' not in href:
                                        continue
                                        
                                    video_id = href.split('watch?v=')[-1].split('&')[0]
                                    if not video_id:
                                        continue
                                    
                                    # Get title
                                    title_elem = element.find(['h4', 'h3', 'span'], class_=['compact-media-item-headline', 'title'])
                                    title = title_elem.text.strip() if title_elem else ''
                                    if not title:
                                        continue
                                    
                                    # Get thumbnail
                                    thumbnail = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
                                    
                                    # Get duration
                                    duration = 'Unknown'
                                    duration_elem = element.find('span', class_='compact-media-item-metadata')
                                    if duration_elem:
                                        duration = duration_elem.text.strip()
                                    
                                    results.append({
                                        'title': title,
                                        'url': f"https://www.youtube.com/watch?v={video_id}",
                                        'thumbnail': thumbnail,
                                        'duration': duration,
                                        'platform': 'YouTube Mobile',
                                        'description': title,
                                        'source': 'YouTube'
                                    })
                                    logger.debug(f"Added YouTube Mobile result: {title}")
                                    
                                except Exception as e:
                                    logger.error(f"Error processing YouTube Mobile result: {str(e)}")
                                    continue
                
                await asyncio.sleep(1)  # Respect rate limits
                
        except Exception as e:
            logger.error(f"Error searching YouTube Mobile: {str(e)}")
        
        logger.info(f"Found {len(results)} results from YouTube Mobile")
        return results[:75]

    async def _search_bing_videos(self, query: str) -> List[Dict]:
        """Search for videos using Bing Video Search."""
        results = []
        try:
            # Search multiple pages
            for offset in range(0, 100, 25):  # Get up to 100 results
                if len(results) >= 75:
                    break
                
                search_url = f"https://www.bing.com/videos/search?q={quote(query)}&first={offset}"
                logger.info(f"Searching Bing videos offset {offset}: {search_url}")
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(search_url, headers=self.headers) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Try multiple selectors for video elements
                            video_elements = soup.find_all('div', class_='dg_u')
                            if not video_elements:
                                video_elements = soup.find_all('div', class_='mc_vtvc')
                            if not video_elements:
                                video_elements = soup.find_all('div', class_='mc_vtvc_meta')
                                
                            logger.info(f"Found {len(video_elements)} video elements on Bing offset {offset}")
                            
                            for element in video_elements:
                                try:
                                    if len(results) >= 75:
                                        break
                                    
                                    # Try multiple ways to get title
                                    title = None
                                    title_elem = element.find(['div', 'span'], class_=['mc_vtvc_title', 'title'])
                                    if title_elem:
                                        title = title_elem.text.strip()
                                    
                                    # Try finding URL
                                    video_url = None
                                    link = element.find('a', href=True)
                                    if link:
                                        video_url = link.get('href', '')
                                    
                                    # Skip if we couldn't find essential info
                                    if not title or not video_url:
                                        logger.debug(f"Skipping Bing result - missing title or URL")
                                        continue
                                    
                                    # Ensure URL is absolute
                                    if video_url and not video_url.startswith('http'):
                                        video_url = f"https://www.bing.com{video_url}"
                                    
                                    # Get thumbnail
                                    thumbnail = None
                                    img = element.find('img')
                                    if img:
                                        thumbnail = img.get('src') or img.get('data-src')
                                    
                                    # Get duration if available
                                    duration = 'Unknown'
                                    duration_elem = element.find(['div', 'span'], class_=['mc_vtvc_duration', 'duration'])
                                    if duration_elem:
                                        duration = duration_elem.text.strip()
                                    
                                    results.append({
                                        'title': title,
                                        'url': video_url,
                                        'thumbnail': thumbnail,
                                        'duration': duration,
                                        'platform': 'Bing',
                                        'description': title,
                                        'source': 'Bing'
                                    })
                                    logger.debug(f"Added Bing result: {title}")
                                    
                                except Exception as e:
                                    logger.error(f"Error processing Bing result: {str(e)}")
                                    continue
                
                await asyncio.sleep(1)  # Respect rate limits
                
        except Exception as e:
            logger.error(f"Error searching Bing: {str(e)}")
        
        logger.info(f"Found {len(results)} results from Bing")
        return results[:75]

    async def _search_bing_videos_uk(self, query: str) -> List[Dict]:
        """Search for videos using Bing UK Video Search."""
        results = []
        try:
            # Search multiple pages
            for offset in range(0, 100, 25):  # Get up to 100 results
                if len(results) >= 75:
                    break
                
                search_url = f"https://www.bing.co.uk/videos/search?q={quote(query)}&first={offset}"
                logger.info(f"Searching Bing UK videos offset {offset}: {search_url}")
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(search_url, headers=self.headers) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Try multiple selectors for video elements
                            video_elements = soup.find_all('div', class_='dg_u')
                            if not video_elements:
                                video_elements = soup.find_all('div', class_='mc_vtvc')
                                
                            logger.info(f"Found {len(video_elements)} video elements on Bing UK offset {offset}")
                            
                            for element in video_elements:
                                try:
                                    if len(results) >= 75:
                                        break
                                    
                                    # Try multiple ways to get title
                                    title = None
                                    title_elem = element.find(['div', 'span'], class_=['mc_vtvc_title', 'title'])
                                    if title_elem:
                                        title = title_elem.text.strip()
                                    
                                    # Try finding URL
                                    video_url = None
                                    link = element.find('a', href=True)
                                    if link:
                                        video_url = link.get('href', '')
                                    
                                    # Skip if we couldn't find essential info
                                    if not title or not video_url:
                                        logger.debug(f"Skipping Bing UK result - missing title or URL")
                                        continue
                                    
                                    # Ensure URL is absolute
                                    if video_url and not video_url.startswith('http'):
                                        video_url = f"https://www.bing.co.uk{video_url}"
                                    
                                    # Get thumbnail
                                    thumbnail = None
                                    img = element.find('img')
                                    if img:
                                        thumbnail = img.get('src') or img.get('data-src')
                                    
                                    # Get duration if available
                                    duration = 'Unknown'
                                    duration_elem = element.find(['div', 'span'], class_=['mc_vtvc_duration', 'duration'])
                                    if duration_elem:
                                        duration = duration_elem.text.strip()
                                    
                                    results.append({
                                        'title': title,
                                        'url': video_url,
                                        'thumbnail': thumbnail,
                                        'duration': duration,
                                        'platform': 'Bing UK',
                                        'description': title,
                                        'source': 'Bing'
                                    })
                                    logger.debug(f"Added Bing UK result: {title}")
                                    
                                except Exception as e:
                                    logger.error(f"Error processing Bing UK result: {str(e)}")
                                    continue
                
                await asyncio.sleep(1)  # Respect rate limits
                
        except Exception as e:
            logger.error(f"Error searching Bing UK: {str(e)}")
        
        logger.info(f"Found {len(results)} results from Bing UK")
        return results[:75]

class VideoSearchCrawlerRunner:
    async def run_both_crawlers(self, query: str):
        crawler1 = VideoSearchCrawler(query)
        crawler2 = VideoSearchCrawlerOriginal(query)
        
        # Run both crawlers concurrently
        await asyncio.gather(
            crawler1.collect_results(),
            crawler2.collect_results()
        )

def setup_routes(app, socketio):
    """Set up Flask routes and Socket.IO event handlers"""
    
    # Track search status
    search_in_progress = False
    
    @socketio.on('connect')
    def handle_connect():
        logger.info("Client connected")
        emit('connected', {'status': 'Connected to server'})

    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info("Client disconnected")

    @socketio.on('search_query')
    def handle_search_query(data):
        """Handle incoming search queries"""
        nonlocal search_in_progress
        
        try:
            logger.info(f"Received search query: {json.dumps(data, indent=2)}")
            
            if search_in_progress:
                logger.warning("Search already in progress")
                emit('search_error', {'error': 'A search is already in progress'})
                return
            
            query = data.get('query', '').strip()
            if not query:
                logger.warning("Empty query received")
                emit('search_error', {'error': 'Please enter a search query'})
                return

            logger.debug(f"Attempting to insert query into database: {query}")  # Debug log
            try:
                cursor = db_connection.cursor()
                cursor.execute("INSERT INTO search_history (query) VALUES (?)", (query,))
                db_connection.commit()
            except sqlite3.Error as e:
                logger.error(f"Failed to insert query: {str(e)}")
                logger.error(f"Database error: {e.args[0]}")
                emit('search_error', {'error': 'Failed to log search query'})
                return
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                logger.error(f"Error details: {e.__dict__}")
                emit('search_error', {'error': 'Failed to log search query'})
                return
            
            search_in_progress = True
            logger.info(f"Starting search for: {query}")
            
            # Notify client
            emit('search_started', {
                'query': query,
                'message': f'Starting search for: {query}'
            })
            
            # Create crawler and run search
            try:
                crawler = VideoSearchCrawlerOriginal(query)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                all_results = loop.run_until_complete(crawler.collect_results())
                loop.close()
                
                # Process and emit results
                processed_results = []
                for result in all_results:
                    processed_result = {
                        'url': result.get('url', ''),
                        'title': result.get('title', 'Untitled Video'),
                        'description': result.get('description', ''),
                        'thumbnail': result.get('thumbnail', ''),
                        'source': result.get('source', 'Unknown'),
                        'duration': result.get('duration', 'Unknown'),
                        'type': 'video'
                    }
                    processed_results.append(processed_result)
                    # Emit each result as it's processed
                    emit('new_result', {'result': processed_result})
                
                logger.info(f"Search completed with {len(processed_results)} results")
                emit('search_completed', {
                    'results': processed_results,
                    'total': len(processed_results),
                    'query': query
                })
                
            except Exception as e:
                logger.error(f"Search error: {str(e)}")
                emit('search_error', {'error': str(e)})
                
            finally:
                search_in_progress = False
                
        except Exception as e:
            logger.error(f"Error handling search query: {str(e)}")
            emit('search_error', {'error': str(e)})