import os
import re
import json
import random
import asyncio
import logging
import aiohttp
import requests
import html2text
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin, quote, urlparse
from typing import List, Dict, Any
from flask_socketio import emit
from flask import request, jsonify
from flask_cors import CORS
import yt_dlp
import sqlite3

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Establish a database connection
db_connection = sqlite3.connect('search_history.db')
cursor = db_connection.cursor()

# Create the search history table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS search_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT NOT NULL,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
    );
''')
db_connection.commit()

def insert_search_query(query):
    logger.debug(f"Inserting query into database: {query}")  # Debug log
    cursor = db_connection.cursor()
    try:
        cursor.execute("INSERT INTO search_history (query) VALUES (?)", (query,))
        db_connection.commit()
        logger.debug("Query inserted successfully.")
    except sqlite3.Error as e:
        logger.error(f"Failed to insert query: {str(e)}")
        logger.error(f"Database error: {e.args[0]}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(f"Error details: {e.__dict__}")

class WebSearchCrawler:
    def __init__(self, base_directory: str, topic: str = None):
        self.base_directory = base_directory
        self.main_topic = topic
        self.search_results = []
        self.seen_links = set()
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
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
            tasks = [
                self._search_youtube(self.main_topic),
                self._search_youtube_mobile(self.main_topic),
                self._search_bing_videos(self.main_topic),
                self._search_bing_videos_uk(self.main_topic),
                self.search_videos_on_platforms(self.main_topic)
            ]
            results = await asyncio.gather(*tasks)
            for engine_results in results:
                if engine_results:
                    all_results.extend(engine_results['results'])
                    logger.info(f"Found {engine_results['count']} results from {engine_results['results'][0]['platform'] if engine_results['results'] else 'Unknown'}")
            random.shuffle(all_results)
            return all_results
        except Exception as e:
            logger.error(f"Error in collect_results: {str(e)}")
            raise

    async def search_videos_on_platforms(self, query: str, page: int = 1, limit: int = 10) -> Dict[str, Any]:
        """Search for videos across various platforms without using APIs, with pagination."""
        results = []
        seen_links = set()  # To track seen video URLs
        try:
            # YouTube Search
            youtube_results = await self._search_youtube(query)
            for video in youtube_results:
                if video['url'] not in seen_links:
                    video_id = video['url'].split('v=')[-1]
                    video['embed'] = f'<iframe width="560" height="315" src="https://www.youtube.com/embed/{video_id}" frameborder="0" allowfullscreen></iframe>'
                    results.append(video)
                    seen_links.add(video['url'])

            # YouTube Mobile Search
            youtube_mobile_results = await self._search_youtube_mobile(query)
            for video in youtube_mobile_results:
                if video['url'] not in seen_links:
                    video_id = video['url'].split('v=')[-1]
                    video['embed'] = f'<iframe width="560" height="315" src="https://www.youtube.com/embed/{video_id}" frameborder="0" allowfullscreen></iframe>'
                    results.append(video)
                    seen_links.add(video['url'])

            # Bing Video Search
            bing_results = await self._search_bing_videos(query)
            for video in bing_results:
                if video['url'] not in seen_links:
                    video['embed'] = f'<iframe width="560" height="315" src="{video["url"]}" frameborder="0" allowfullscreen></iframe>'
                    results.append(video)
                    seen_links.add(video['url'])

            # Bing UK Video Search
            bing_uk_results = await self._search_bing_videos_uk(query)
            for video in bing_uk_results:
                if video['url'] not in seen_links:
                    video['embed'] = f'<iframe width="560" height="315" src="{video["url"]}" frameborder="0" allowfullscreen></iframe>'
                    results.append(video)
                    seen_links.add(video['url'])

            # Pagination logic
            total_results = len(results)
            start_index = (page - 1) * limit
            end_index = start_index + limit
            paginated_results = results[start_index:end_index]

            return {'count': total_results, 'results': paginated_results}
        except Exception as e:
            logger.error(f"Error searching platforms: {str(e)}")
            return {'count': 0, 'results': []}

    async def _search_youtube(self, query: str) -> List[Dict]:
        """Search for videos on YouTube."""
        results = []
        try:
            sort_params = ['', '&sp=CAI%253D', '&sp=CAM%253D']  # Default, Date, Rating
            for sort_param in sort_params:
                if len(results) >= 75:
                    break
                search_url = f"https://www.youtube.com/results?search_query={quote(query)}{sort_param}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(search_url, headers=self.headers) as response:
                        if response.status == 200:
                            html = await response.text()
                            video_ids = re.findall(r'"videoId":"([^"]+)"', html)
                            video_titles = re.findall(r'"title":{"runs":\[{"text":"([^"]+)"}]}', html)
                            video_durations = re.findall(r'"simpleText":"([0-9:]+)"', html)
                            video_views = re.findall(r'"viewCountText":{"simpleText":"([^"]+)"}', html)
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
            for page in range(1, 4):  # Get up to 3 pages of results
                if len(results) >= 75:
                    break
                search_url = f"https://m.youtube.com/results?search_query={quote(query)}&page={page}"
                logger.info(f"Searching YouTube Mobile page {page}: {search_url}")
                async with aiohttp.ClientSession() as session:
                    async with session.get(search_url, headers=self.headers) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            video_elements = soup.find_all('div', class_='compact-media-item')
                            logger.info(f"Found {len(video_elements)} video elements on YouTube Mobile page {page}")
                            for element in video_elements:
                                try:
                                    if len(results) >= 75:
                                        break
                                    link = element.find('a', href=True)
                                    if not link:
                                        continue
                                    href = link.get('href', '')
                                    if not href or '/watch?v=' not in href:
                                        continue
                                    video_id = href.split('watch?v=')[-1].split('&')[0]
                                    if not video_id:
                                        continue
                                    title_elem = element.find(['h4', 'h3', 'span'], class_=['compact-media-item-headline', 'title'])
                                    title = title_elem.text.strip() if title_elem else ''
                                    if not title:
                                        continue
                                    thumbnail = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
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
                                    title = None
                                    title_elem = element.find(['div', 'span'], class_=['mc_vtvc_title', 'title'])
                                    if title_elem:
                                        title = title_elem.text.strip()
                                    video_url = None
                                    link = element.find('a', href=True)
                                    if link:
                                        video_url = link.get('href', '')
                                    if not title or not video_url:
                                        logger.debug(f"Skipping Bing result - missing title or URL")
                                        continue
                                    if video_url and not video_url.startswith('http'):
                                        video_url = f"https://www.bing.com{video_url}"
                                    thumbnail = None
                                    img = element.find('img')
                                    if img:
                                        thumbnail = img.get('src') or img.get('data-src')
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
                            video_elements = soup.find_all('div', class_='dg_u')
                            if not video_elements:
                                video_elements = soup.find_all('div', class_='mc_vtvc')
                            logger.info(f"Found {len(video_elements)} video elements on Bing UK offset {offset}")
                            for element in video_elements:
                                try:
                                    if len(results) >= 75:
                                        break
                                    title = None
                                    title_elem = element.find(['div', 'span'], class_=['mc_vtvc_title', 'title'])
                                    if title_elem:
                                        title = title_elem.text.strip()
                                    video_url = None
                                    link = element.find('a', href=True)
                                    if link:
                                        video_url = link.get('href', '')
                                    if not title or not video_url:
                                        logger.debug(f"Skipping Bing UK result - missing title or URL")
                                        continue
                                    if video_url and not video_url.startswith('http'):
                                        video_url = f"https://www.bing.co.uk{video_url}"
                                    thumbnail = None
                                    img = element.find('img')
                                    if img:
                                        thumbnail = img.get('src') or img.get('data-src')
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

    def search_directories(self):
        """Search through open directories and return a list of video file and directory names."""
        results = []
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv']
        for root, dirs, files in os.walk(self.base_directory):
            for name in files:
                if any(name.lower().endswith(ext) for ext in video_extensions):
                    results.append(os.path.join(root, name))
        return results

    def advanced_search(self, query):
        """Perform an advanced search based on the provided query for video files."""
        results = []
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv']
        for root, dirs, files in os.walk(self.base_directory):
            for name in files:
                if query.lower() in name.lower() and any(name.lower().endswith(ext) for ext in video_extensions):
                    results.append(os.path.join(root, name))
        return results

def fetch_search_history_from_db():
    cursor = db_connection.cursor()
    cursor.execute("SELECT * FROM search_history ORDER BY timestamp DESC")
    return cursor.fetchall()

def setup_routes(app, socketio):
    """Set up Flask routes and Socket.IO event handlers"""
    
    # Track search status
    search_in_progress = False
    
    # Allow CORS for the specified frontend domain
    CORS(app, resources={r"/*": {"origins": "https://youtube-qotc.onrender.com"}})

    @app.route('/search_directories', methods=['GET'])
    def search_directories():
        base_directory = request.args.get('base_directory', '.')  # Default to current directory
        results = []
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv']
        for root, dirs, files in os.walk(base_directory):
            for name in files:
                if any(name.lower().endswith(ext) for ext in video_extensions):
                    results.append(os.path.join(root, name))
        return {'results': results}

    @app.route('/advanced_search', methods=['GET'])
    def advanced_search():
        query = request.args.get('query', '')
        base_directory = request.args.get('base_directory', '.')  # Default to current directory
        results = []
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv']
        for root, dirs, files in os.walk(base_directory):
            for name in files:
                if query.lower() in name.lower() and any(name.lower().endswith(ext) for ext in video_extensions):
                    results.append(os.path.join(root, name))
        return {'results': results}

    @app.route('/search_videos', methods=['GET'])
    def search_videos():
        data = request.args
        query = data.get('query')
        page = int(data.get('page', 1))  # Convert to integer
        limit = int(data.get('limit', 10))  # Convert to integer

        logger.debug(f"Searching videos with query: {query}, page: {page}, limit: {limit}")
        
        # Implement video search logic here
        results = perform_video_search(query, page, limit)
        return jsonify(results)


    def perform_video_search(query, page, limit):
        api_key = os.getenv('YOUTUBE_API_KEY')  # Retrieve the API key from environment variables
        url = f'https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&maxResults={limit}&key={api_key}'
        
        if page > 1:
            url += f"&pageToken={page}"  # Add pageToken only if it's not the first page
        
        logger.debug(f"Performing video search for query: {query}, page: {page}, limit: {limit}")
        
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            results = []
            for item in data.get('items', []):
                if item['id']['kind'] == 'youtube#video':  # Check if the item is a video
                    results.append({
                        'title': item['snippet']['title'],
                        'videoId': item['id']['videoId']
                    })
            next_page_token = data.get('nextPageToken')  # Capture the nextPageToken
            logger.debug(f"Search results: {results}, nextPageToken: {next_page_token}")
            return {"results": results, "count": len(results), "nextPageToken": next_page_token}
        else:
            logger.error(f"Error fetching from YouTube API: {response.status_code} - {response.text}")
            return {"results": [], "count": 0}

    @app.route('/download_videos', methods=['POST'])
    def download_videos():
        data = request.json
        app.logger.debug(f"Received data: {data}")
        urls = data.get('urls', [])
        location = data.get('location', os.path.expanduser('~/Downloads'))  # Get the location from the request
        cookie_file = data.get('cookiefile')  # Get the cookies file path from the request

        if not cookie_file or not os.path.exists(cookie_file):
            return jsonify({'status': 'error', 'message': 'The required cookies file is not being used or does not exist. Please provide a valid path.\n\nInstructions for Exporting Cookies:\n1. For Chrome: Use the EditThisCookie extension to export cookies.\n2. For Firefox: Use the Cookies.txt extension to export cookies.\n3. For Edge: Use the EditThisCookie extension or sync with Chrome to export cookies.'}), 400

        # Initialize ydl_opts
        ydl_opts = {
            'outtmpl': os.path.join(location, '%(title)s.%(ext)s'),  # Save to provided location
        }

        # If a cookie file is provided and exists, add it to options
        if cookie_file and os.path.exists(cookie_file):
            ydl_opts['cookiefile'] = cookie_file

        try:
            for url in urls:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
        
            return jsonify({'status': 'success', 'message': 'Downloads started.'})
        except Exception as e:
            app.logger.error(f"Error downloading videos: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @app.route('/search_history', methods=['GET'])
    def get_search_history():
        logger.debug("Fetching search history.")
        try:
            results = fetch_search_history_from_db()  # Fetch history from the database
            logger.debug(f"Search history retrieved: {results}")
            return jsonify(results)  # Send results as JSON
        except Exception as e:
            logger.error(f"Error fetching search history: {str(e)}")
            return jsonify({'error': 'Failed to fetch search history'}), 500

    @app.route('/search', methods=['POST'])
    def perform_search():
        logger.debug("Perform search function called.")
        data = request.json
        logger.debug(f"Received data: {data}")  # Log the received data
        query = data.get('query')
        
        if not query:
            emit('search_error', {'error': 'Please enter a search query'})
            return
        
        logger.debug(f"Attempting to insert query into database: {query}")  # Debug log
        try:
            insert_search_query(query)  # Log the search query
            logger.debug("Query inserted successfully.")
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
        
        # Perform search logic
        crawler = WebSearchCrawler('.', query)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(crawler.collect_results())
        except Exception as e:
            logger.error(f"Error collecting results: {str(e)}")
            emit('search_error', {'error': 'Failed to collect results'})
            loop.close()
            return
        loop.close()
        
        if results:
            return jsonify({'status': 'success', 'data': results}), 200
        else:
            return jsonify({'status': 'error', 'message': 'No results found.'}), 404

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
                crawler = WebSearchCrawler('.', query)
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
                        'type': 'video',
                        'embed': result.get('embed', '')
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