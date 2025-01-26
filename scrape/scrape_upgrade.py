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
from flask import send_from_directory
from flask_socketio import emit

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class VideoSearchCrawler:
    def __init__(self, topic: str):
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

    def _get_source_from_url(self, url: str) -> str:
        """Get the source name from a URL."""
        if not url:
            return 'Unknown'
            
        url_lower = url.lower()
        
        # Video platforms
        if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'YouTube'
        if 'vimeo.com' in url_lower:
            return 'Vimeo'
        if 'dailymotion.com' in url_lower or 'dai.ly' in url_lower:
            return 'Dailymotion'
            
        # Social platforms
        if 'facebook.com' in url_lower:
            return 'Facebook'
        if 'twitter.com' in url_lower:
            return 'Twitter'
        if 'instagram.com' in url_lower:
            return 'Instagram'
        if 'linkedin.com' in url_lower:
            return 'LinkedIn'
            
        # News and media
        if 'cnn.com' in url_lower:
            return 'CNN'
        if 'bbc.co.uk' in url_lower or 'bbc.com' in url_lower:
            return 'BBC'
        if 'nytimes.com' in url_lower:
            return 'New York Times'
        if 'reuters.com' in url_lower:
            return 'Reuters'
            
        # Tech sites
        if 'github.com' in url_lower:
            return 'GitHub'
        if 'stackoverflow.com' in url_lower:
            return 'Stack Overflow'
        if 'medium.com' in url_lower:
            return 'Medium'
        if 'dev.to' in url_lower:
            return 'DEV Community'
            
        # Education
        if '.edu' in url_lower:
            return 'Educational Institution'
        if 'wikipedia.org' in url_lower:
            return 'Wikipedia'
        if 'coursera.org' in url_lower:
            return 'Coursera'
        if 'udemy.com' in url_lower:
            return 'Udemy'
            
        try:
            # Extract domain for unknown sites
            domain = urlparse(url).netloc
            if domain:
                # Remove www. and get the main domain
                domain = domain.replace('www.', '')
                # Capitalize first letter of each word
                return ' '.join(word.capitalize() for word in domain.split('.')[0].split('-'))
        except:
            pass
            
        return 'Unknown'

    async def collect_results(self, search_types: Dict[str, bool]):
        """Collect video and website results based on search types"""
        try:
            logger.info(f"Starting search for: {self.main_topic}")
            all_results = []
            tasks = []

            # Add video search tasks
            if search_types.get('videos', True):
                tasks.extend([
                    self._search_youtube(self.main_topic),
                    self._search_youtube_mobile(self.main_topic),
                    self._search_bing_videos(self.main_topic),
                    self._search_bing_videos_uk(self.main_topic),
                    self.search_videos(aiohttp.ClientSession(), self.main_topic),
                    self._search_google_videos(self.main_topic)
                ])

            # Add website search tasks
            if search_types.get('websites', True):
                tasks.extend([
                    # General search engines
                    self._search_google(self.main_topic),
                    self._search_bing(self.main_topic),
                    self._search_duckduckgo(self.main_topic),
                    self._search_yahoo(self.main_topic),
                    self._search_brave(self.main_topic),
                    self._search_qwant(self.main_topic),
                    self._search_ecosia(self.main_topic),
                    # Advanced search engines
                    self._search_scholar(self.main_topic),
                    self._search_semantic(self.main_topic),
                    self._search_base(self.main_topic),
                    self._search_arxiv(self.main_topic),
                    self._search_github(self.main_topic),
                    # Specialized advanced engines
                    self._search_wolfram(self.main_topic),
                    self._search_archive(self.main_topic),
                    self._search_metager(self.main_topic)
                ])

            # Add Google CSE searches
            cse_engines = [
                "006516753008110874046:vzcl7wcfhei",  # CSE 1
                "006516753008110874046:hrhinud6efg",  # CSE 2
                "006516753008110874046:6v9mqdaai6q",  # CSE 3
                "006516753008110874046:wevn3lkn9rr",  # CSE 4
                "006516753008110874046:cfdhwy9o57g"   # CSE 5
            ]
            
            for cx in cse_engines:
                tasks.append(self._search_google_cse(self.main_topic, cx))

            # Run all searches in parallel with increased timeout
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle any exceptions
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Search error: {str(result)}")
                    continue
                if isinstance(result, list):
                    all_results.extend(result)

            # Remove duplicates while preserving order
            seen = set()
            unique_results = []
            for result in all_results:
                url = result.get('url', '')
                if url and url not in seen:
                    seen.add(url)
                    unique_results.append(result)

            logger.info(f"Total unique results: {len(unique_results)}")
            return unique_results

        except Exception as e:
            logger.error(f"Error collecting results: {str(e)}")
            return []

    async def _search_youtube(self, query: str) -> List[Dict]:
        """Search for videos on YouTube"""
        results = []
        try:
            search_url = f"https://www.youtube.com/results?search_query={quote(query)}"
            logger.info(f"Searching YouTube: {search_url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Find video elements
                        video_elements = soup.find_all('div', {'class': ['yt-lockup-video', 'yt-lockup-tile']})
                        logger.info(f"Found {len(video_elements)} video elements")
                        
                        for element in video_elements:
                            try:
                                if len(results) >= 75:
                                    break
                                
                                # Get video ID
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
                                title_elem = element.find(['h3', 'span'], class_=['yt-lockup-title', 'title'])
                                title = title_elem.text.strip() if title_elem else ''
                                if not title:
                                    continue
                                
                                # Get thumbnail
                                thumbnail = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
                                
                                # Get duration
                                duration = 'Unknown'
                                duration_elem = element.find('span', class_=['video-time', 'duration'])
                                if duration_elem:
                                    duration = duration_elem.text.strip()
                                
                                results.append({
                                    'type': 'video',
                                    'title': title,
                                    'url': f"https://www.youtube.com/watch?v={video_id}",
                                    'thumbnail': thumbnail,
                                    'duration': duration,
                                    'platform': 'YouTube',
                                    'description': title,
                                    'source': 'YouTube'
                                })
                                logger.debug(f"Added YouTube result: {title}")
                                
                            except Exception as e:
                                logger.error(f"Error processing YouTube result: {str(e)}")
                                continue
                
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
                                        'type': 'video',
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
                                        'type': 'video',
                                        'title': title,
                                        'url': video_url,
                                        'thumbnail': thumbnail,
                                        'duration': duration,
                                        'platform': 'Bing',
                                        'description': title,
                                        'source': self._get_source_from_url(video_url)
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
                                        'type': 'video',
                                        'title': title,
                                        'url': video_url,
                                        'thumbnail': thumbnail,
                                        'duration': duration,
                                        'platform': 'Bing UK',
                                        'description': title,
                                        'source': self._get_source_from_url(video_url)
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

    async def _search_bing(self, query: str) -> List[Dict]:
        """Search for websites using Bing Search."""
        results = []
        try:
            search_url = f"https://www.bing.com/search?q={quote(query)}"
            logger.info(f"Searching Bing: {search_url}")

            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')

                        # Find search results
                        search_results = soup.find_all('li', class_='b_algo')
                        logger.info(f"Found {len(search_results)} website results from Bing")

                        for result in search_results:
                            try:
                                # Get title and URL
                                title_elem = result.find('h2')
                                link = title_elem.find('a')
                                if not title_elem or not link:
                                    continue

                                title = title_elem.text.strip()
                                url = link.get('href', '')

                                # Skip if no valid URL
                                if not url.startswith('http'):
                                    continue

                                # Get description
                                description = ''
                                desc_elem = result.find('div', class_='b_caption')
                                if desc_elem:
                                    description = desc_elem.text.strip()

                                # Get favicon
                                favicon = f"https://www.bing.com/s2/favicons?domain={quote(url)}"

                                results.append({
                                    'type': 'website',
                                    'title': title,
                                    'url': url,
                                    'description': description,
                                    'favicon': favicon,
                                    'platform': 'Bing',
                                    'source': self._get_source_from_url(url)
                                })

                            except Exception as e:
                                logger.error(f"Error processing Bing result: {str(e)}")
                                continue

        except Exception as e:
            logger.error(f"Error searching Bing: {str(e)}")

        return results[:100]

    async def _search_duckduckgo(self, query: str) -> List[Dict]:
        """Search for websites using DuckDuckGo Search."""
        results = []
        try:
            # DuckDuckGo HTML search URL
            search_url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
            logger.info(f"Searching DuckDuckGo: {search_url}")

            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')

                        # Find search results
                        search_results = soup.find_all('div', class_='result')
                        logger.info(f"Found {len(search_results)} website results from DuckDuckGo")

                        for result in search_results:
                            try:
                                # Get title and URL
                                title_elem = result.find('a', class_='result__a')
                                if not title_elem:
                                    continue

                                title = title_elem.text.strip()
                                url = title_elem.get('href', '')

                                # Skip if no valid URL
                                if not url.startswith('http'):
                                    continue

                                # Get description
                                description = ''
                                desc_elem = result.find('a', class_='result__snippet')
                                if desc_elem:
                                    description = desc_elem.text.strip()

                                # Get favicon
                                parsed_url = urlparse(url)
                                favicon = f"https://icons.duckduckgo.com/ip3/{parsed_url.netloc}.ico"

                                results.append({
                                    'type': 'website',
                                    'title': title,
                                    'url': url,
                                    'description': description,
                                    'favicon': favicon,
                                    'platform': 'DuckDuckGo',
                                    'source': self._get_source_from_url(url)
                                })

                            except Exception as e:
                                logger.error(f"Error processing DuckDuckGo result: {str(e)}")
                                continue

        except Exception as e:
            logger.error(f"Error searching DuckDuckGo: {str(e)}")

        return results[:100]

    async def _search_google(self, query: str) -> List[Dict]:
        """Search for websites using Google Search."""
        results = []
        try:
            search_url = f"https://www.google.com/search?q={quote(query)}"
            logger.info(f"Searching Google: {search_url}")

            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')

                        # Find search results
                        search_results = soup.find_all('div', class_='g')
                        logger.info(f"Found {len(search_results)} website results from Google")

                        for result in search_results:
                            try:
                                # Get title and URL
                                title_elem = result.find('h3')
                                link = result.find('a')
                                if not title_elem or not link:
                                    continue

                                title = title_elem.text.strip()
                                url = link.get('href', '')

                                # Skip if no valid URL
                                if not url.startswith('http'):
                                    continue

                                # Get description
                                description = ''
                                desc_elem = result.find('div', class_=['VwiC3b', 'yXK7lf'])
                                if desc_elem:
                                    description = desc_elem.text.strip()

                                # Get favicon
                                favicon = f"https://www.google.com/s2/favicons?domain={quote(url)}"

                                results.append({
                                    'type': 'website',
                                    'title': title,
                                    'url': url,
                                    'description': description,
                                    'favicon': favicon,
                                    'platform': 'Google',
                                    'source': self._get_source_from_url(url)
                                })

                            except Exception as e:
                                logger.error(f"Error processing Google result: {str(e)}")
                                continue

        except Exception as e:
            logger.error(f"Error searching Google: {str(e)}")

        return results[:100]

    async def _search_yahoo(self, query: str) -> List[Dict]:
        """Search for websites using Yahoo Search."""
        results = []
        try:
            search_url = f"https://search.yahoo.com/search?p={quote(query)}"
            logger.info(f"Searching Yahoo: {search_url}")

            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')

                        # Find search results
                        search_results = soup.find_all('div', class_='algo')
                        logger.info(f"Found {len(search_results)} website results from Yahoo")

                        for result in search_results:
                            try:
                                # Get title and URL
                                title_elem = result.find('h3')
                                link = result.find('a')
                                if not title_elem or not link:
                                    continue

                                title = title_elem.text.strip()
                                url = link.get('href', '')

                                # Skip if no valid URL
                                if not url.startswith('http'):
                                    continue

                                # Get description
                                description = ''
                                desc_elem = result.find('div', class_='compText')
                                if desc_elem:
                                    description = desc_elem.text.strip()

                                # Get favicon
                                parsed_url = urlparse(url)
                                favicon = f"https://s.yimg.com/favicon/{parsed_url.netloc}"

                                results.append({
                                    'type': 'website',
                                    'title': title,
                                    'url': url,
                                    'description': description,
                                    'favicon': favicon,
                                    'platform': 'Yahoo',
                                    'source': self._get_source_from_url(url)
                                })

                            except Exception as e:
                                logger.error(f"Error processing Yahoo result: {str(e)}")
                                continue

        except Exception as e:
            logger.error(f"Error searching Yahoo: {str(e)}")

        return results[:100]

    async def _search_brave(self, query: str) -> List[Dict]:
        """Search for websites using Brave Search."""
        results = []
        try:
            search_url = f"https://search.brave.com/search?q={quote(query)}"
            logger.info(f"Searching Brave: {search_url}")

            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')

                        # Find search results
                        search_results = soup.find_all('div', class_='snippet')
                        logger.info(f"Found {len(search_results)} website results from Brave")

                        for result in search_results:
                            try:
                                # Get title and URL
                                title_elem = result.find('a', class_='title')
                                if not title_elem:
                                    continue

                                title = title_elem.text.strip()
                                url = title_elem.get('href', '')

                                # Skip if no valid URL
                                if not url.startswith('http'):
                                    continue

                                # Get description
                                description = ''
                                desc_elem = result.find('div', class_='snippet-description')
                                if desc_elem:
                                    description = desc_elem.text.strip()

                                # Get favicon
                                parsed_url = urlparse(url)
                                favicon = f"https://brave.com/favicon/s2?domain={quote(parsed_url.netloc)}"

                                results.append({
                                    'type': 'website',
                                    'title': title,
                                    'url': url,
                                    'description': description,
                                    'favicon': favicon,
                                    'platform': 'Brave',
                                    'source': self._get_source_from_url(url)
                                })

                            except Exception as e:
                                logger.error(f"Error processing Brave result: {str(e)}")
                                continue

        except Exception as e:
            logger.error(f"Error searching Brave: {str(e)}")

        return results[:100]

    async def _search_qwant(self, query: str) -> List[Dict]:
        """Search for websites using Qwant Search."""
        results = []
        try:
            search_url = f"https://www.qwant.com/?q={quote(query)}&t=web"
            logger.info(f"Searching Qwant: {search_url}")

            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')

                        # Find search results
                        search_results = soup.find_all(['article', 'div'], class_=['result', 'web-result'])
                        logger.info(f"Found {len(search_results)} website results from Qwant")

                        for result in search_results:
                            try:
                                # Get title and URL
                                title_elem = result.find(['h2', 'h3'])
                                link = result.find('a')
                                if not title_elem or not link:
                                    continue

                                title = title_elem.text.strip()
                                url = link.get('href', '')

                                # Skip if no valid URL
                                if not url.startswith('http'):
                                    continue

                                # Get description
                                description = ''
                                desc_elem = result.find(['p', 'div'], class_=['result-description', 'description'])
                                if desc_elem:
                                    description = desc_elem.text.strip()

                                # Get favicon
                                parsed_url = urlparse(url)
                                favicon = f"https://www.google.com/s2/favicons?domain={quote(parsed_url.netloc)}"

                                results.append({
                                    'type': 'website',
                                    'title': title,
                                    'url': url,
                                    'description': description,
                                    'favicon': favicon,
                                    'platform': 'Qwant',
                                    'source': self._get_source_from_url(url)
                                })

                            except Exception as e:
                                logger.error(f"Error processing Qwant result: {str(e)}")
                                continue

        except Exception as e:
            logger.error(f"Error searching Qwant: {str(e)}")

        return results[:100]

    async def _search_ecosia(self, query: str) -> List[Dict]:
        """Search for websites using Ecosia Search."""
        results = []
        try:
            search_url = f"https://www.ecosia.org/search?q={quote(query)}"
            logger.info(f"Searching Ecosia: {search_url}")

            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')

                        # Find search results
                        search_results = soup.find_all(['article', 'div'], class_=['result', 'web-result', 'card-web'])
                        logger.info(f"Found {len(search_results)} website results from Ecosia")

                        for result in search_results:
                            try:
                                # Get title and URL
                                title_elem = result.find(['h2', 'a'], class_=['result-title', 'title'])
                                link = result.find('a')
                                if not title_elem:
                                    continue

                                title = title_elem.text.strip()
                                url = link.get('href', '') if link else ''

                                # Skip if no valid URL
                                if not url.startswith('http'):
                                    continue

                                # Get description
                                description = ''
                                desc_elem = result.find(['p', 'div'], class_=['result-description', 'description', 'snippet'])
                                if desc_elem:
                                    description = desc_elem.text.strip()

                                # Get favicon
                                parsed_url = urlparse(url)
                                favicon = f"https://www.google.com/s2/favicons?domain={quote(parsed_url.netloc)}"

                                results.append({
                                    'type': 'website',
                                    'title': title,
                                    'url': url,
                                    'description': description,
                                    'favicon': favicon,
                                    'platform': 'Ecosia',
                                    'source': self._get_source_from_url(url)
                                })

                            except Exception as e:
                                logger.error(f"Error processing Ecosia result: {str(e)}")
                                continue

        except Exception as e:
            logger.error(f"Error searching Ecosia: {str(e)}")

        return results[:100]

    async def _search_scholar(self, query: str) -> List[Dict]:
        """Search for academic papers using Google Scholar."""
        results = []
        try:
            search_url = f"https://scholar.google.com/scholar?q={quote(query)}"
            logger.info(f"Searching Google Scholar: {search_url}")

            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')

                        # Find search results
                        search_results = soup.find_all('div', class_='gs_r')
                        logger.info(f"Found {len(search_results)} academic results from Google Scholar")

                        for result in search_results:
                            try:
                                # Get title and URL
                                title_elem = result.find('h3', class_='gs_rt')
                                if not title_elem:
                                    continue

                                title = title_elem.text.strip()
                                link = title_elem.find('a')
                                url = link.get('href', '') if link else ''

                                # Skip if no valid URL
                                if not url.startswith('http'):
                                    continue

                                # Get description
                                description = ''
                                desc_elem = result.find('div', class_='gs_rs')
                                if desc_elem:
                                    description = desc_elem.text.strip()

                                # Get authors and publication info
                                authors = ''
                                pub_info = ''
                                meta_elem = result.find('div', class_='gs_a')
                                if meta_elem:
                                    meta_text = meta_elem.text.strip()
                                    parts = meta_text.split('-')
                                    if len(parts) > 1:
                                        authors = parts[0].strip()
                                        pub_info = parts[1].strip()

                                # Get favicon
                                parsed_url = urlparse(url)
                                favicon = f"https://www.google.com/s2/favicons?domain={quote(parsed_url.netloc)}"

                                results.append({
                                    'type': 'website',
                                    'title': title,
                                    'url': url,
                                    'description': f"{description}\nAuthors: {authors}\nPublication: {pub_info}",
                                    'favicon': favicon,
                                    'platform': 'Google Scholar',
                                    'source': self._get_source_from_url(url)
                                })

                            except Exception as e:
                                logger.error(f"Error processing Google Scholar result: {str(e)}")
                                continue

        except Exception as e:
            logger.error(f"Error searching Google Scholar: {str(e)}")

        return results[:100]

    async def _search_semantic(self, query: str) -> List[Dict]:
        """Search for academic papers using Semantic Scholar."""
        results = []
        try:
            search_url = f"https://www.semanticscholar.org/search?q={quote(query)}"
            logger.info(f"Searching Semantic Scholar: {search_url}")

            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')

                        # Find search results
                        search_results = soup.find_all('div', class_=['result-page', 'search-result-item'])
                        logger.info(f"Found {len(search_results)} academic results from Semantic Scholar")

                        for result in search_results:
                            try:
                                # Get title and URL
                                title_elem = result.find(['h2', 'a'], class_='search-result-title')
                                if not title_elem:
                                    continue

                                title = title_elem.text.strip()
                                url = f"https://www.semanticscholar.org{title_elem.get('href', '')}" if title_elem.get('href') else ''

                                # Skip if no valid URL
                                if not url.startswith('http'):
                                    continue

                                # Get description and metadata
                                description = ''
                                abstract_elem = result.find('span', class_='search-result-abstract')
                                if abstract_elem:
                                    description = abstract_elem.text.strip()

                                # Get authors and year
                                authors = []
                                authors_elem = result.find_all('span', class_='author-list')
                                if authors_elem:
                                    authors = [author.text.strip() for author in authors_elem]

                                year = ''
                                year_elem = result.find('span', class_='year')
                                if year_elem:
                                    year = year_elem.text.strip()

                                results.append({
                                    'type': 'website',
                                    'title': title,
                                    'url': url,
                                    'description': f"{description}\nAuthors: {', '.join(authors)}\nYear: {year}",
                                    'favicon': "https://www.semanticscholar.org/img/favicon.png",
                                    'platform': 'Semantic Scholar',
                                    'source': self._get_source_from_url(url)
                                })

                            except Exception as e:
                                logger.error(f"Error processing Semantic Scholar result: {str(e)}")
                                continue

        except Exception as e:
            logger.error(f"Error searching Semantic Scholar: {str(e)}")

        return results[:100]

    async def _search_base(self, query: str) -> List[Dict]:
        """Search for academic content using BASE (Bielefeld Academic Search Engine)."""
        results = []
        try:
            search_url = f"https://www.base-search.net/Search/Results?lookfor={quote(query)}"
            logger.info(f"Searching BASE: {search_url}")

            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')

                        # Find search results
                        search_results = soup.find_all('div', class_=['result-item', 'doia-result'])
                        logger.info(f"Found {len(search_results)} academic results from BASE")

                        for result in search_results:
                            try:
                                # Get title and URL
                                title_elem = result.find(['h3', 'a'], class_='title')
                                if not title_elem:
                                    continue

                                title = title_elem.text.strip()
                                url = title_elem.get('href', '')

                                # Skip if no valid URL
                                if not url.startswith('http'):
                                    continue

                                # Get description
                                description = ''
                                desc_elem = result.find('div', class_='description')
                                if desc_elem:
                                    description = desc_elem.text.strip()

                                # Get metadata
                                metadata = []
                                meta_elems = result.find_all('div', class_=['metadata', 'doctype'])
                                for elem in meta_elems:
                                    metadata.append(elem.text.strip())

                                results.append({
                                    'type': 'website',
                                    'title': title,
                                    'url': url,
                                    'description': f"{description}\n{' | '.join(metadata)}",
                                    'favicon': "https://www.base-search.net/favicon.ico",
                                    'platform': 'BASE',
                                    'source': self._get_source_from_url(url)
                                })

                            except Exception as e:
                                logger.error(f"Error processing BASE result: {str(e)}")
                                continue

        except Exception as e:
            logger.error(f"Error searching BASE: {str(e)}")

        return results[:100]

    async def _search_arxiv(self, query: str) -> List[Dict]:
        """Search for scientific papers on arXiv."""
        results = []
        try:
            search_url = f"https://arxiv.org/search/?query={quote(query)}&searchtype=all"
            logger.info(f"Searching arXiv: {search_url}")

            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')

                        # Find search results
                        search_results = soup.find_all('li', class_='arxiv-result')
                        logger.info(f"Found {len(search_results)} scientific papers from arXiv")

                        for result in search_results:
                            try:
                                # Get title and URL
                                title_elem = result.find('p', class_='title')
                                if not title_elem:
                                    continue

                                title = title_elem.text.strip()
                                link = result.find('a', class_='abstract-full')
                                url = f"https://arxiv.org{link.get('href', '')}" if link else ''

                                # Skip if no valid URL
                                if not url.startswith('http'):
                                    continue

                                # Get abstract
                                description = ''
                                abstract_elem = result.find('p', class_='abstract-full')
                                if abstract_elem:
                                    description = abstract_elem.text.strip()

                                # Get authors and other metadata
                                authors = []
                                authors_elem = result.find('p', class_='authors')
                                if authors_elem:
                                    authors = [author.text.strip() for author in authors_elem.find_all('a')]

                                # Get submission info
                                submitted = ''
                                meta_elem = result.find('p', class_='submission-history')
                                if meta_elem:
                                    submitted = meta_elem.text.strip()

                                results.append({
                                    'type': 'website',
                                    'title': title,
                                    'url': url,
                                    'description': f"{description}\nAuthors: {', '.join(authors)}\n{submitted}",
                                    'favicon': "https://static.arxiv.org/static/browse/0.3.4/images/icons/favicon.ico",
                                    'platform': 'arXiv',
                                    'source': self._get_source_from_url(url)
                                })

                            except Exception as e:
                                logger.error(f"Error processing arXiv result: {str(e)}")
                                continue

        except Exception as e:
            logger.error(f"Error searching arXiv: {str(e)}")

        return results[:100]

    async def _search_github(self, query: str) -> List[Dict]:
        """Search for repositories and code on GitHub."""
        results = []
        try:
            search_url = f"https://github.com/search?q={quote(query)}&type=repositories"
            logger.info(f"Searching GitHub: {search_url}")

            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')

                        # Find search results
                        search_results = soup.find_all('div', class_=['repo-list-item', 'Box-row'])
                        logger.info(f"Found {len(search_results)} repositories from GitHub")

                        for result in search_results:
                            try:
                                # Get title and URL
                                title_elem = result.find(['a', 'h3'], class_='v-align-middle repo-list-name')
                                if not title_elem:
                                    continue

                                title = title_elem.text.strip()
                                url = f"https://github.com{title_elem.get('href', '')}" if title_elem.get('href') else ''

                                # Skip if no valid URL
                                if not url.startswith('http'):
                                    continue

                                # Get description
                                description = ''
                                desc_elem = result.find('p', class_=['repo-list-description', 'color-fg-muted'])
                                if desc_elem:
                                    description = desc_elem.text.strip()

                                # Get repository metadata
                                metadata = []
                                meta_elems = result.find_all(['div', 'span'], class_=['repo-list-meta', 'f6', 'color-fg-muted'])
                                for elem in meta_elems:
                                    metadata.append(elem.text.strip())

                                results.append({
                                    'type': 'website',
                                    'title': title,
                                    'url': url,
                                    'description': f"{description}\n{' | '.join(metadata)}",
                                    'favicon': "https://github.githubassets.com/favicons/favicon.svg",
                                    'platform': 'GitHub',
                                    'source': self._get_source_from_url(url)
                                })

                            except Exception as e:
                                logger.error(f"Error processing GitHub result: {str(e)}")
                                continue

        except Exception as e:
            logger.error(f"Error searching GitHub: {str(e)}")

        return results[:100]

    async def _search_wolfram(self, query: str) -> List[Dict]:
        """Search for computational knowledge using Wolfram Alpha."""
        results = []
        try:
            search_url = f"https://www.wolframalpha.com/input?i={quote(query)}"
            logger.info(f"Searching Wolfram Alpha: {search_url}")

            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')

                        # Find search results
                        search_results = soup.find_all(['section', 'div'], class_=['pod', '_2WrB', '_3B89'])
                        logger.info(f"Found {len(search_results)} computational results from Wolfram Alpha")

                        for result in search_results:
                            try:
                                # Get title
                                title_elem = result.find(['h2', 'div'], class_=['_3f89', 'pod-title'])
                                if not title_elem:
                                    continue

                                title = title_elem.text.strip()
                                url = search_url

                                # Get result content
                                content = ''
                                content_elem = result.find(['div', 'img'], class_=['_3B89', 'pod-content'])
                                if content_elem:
                                    if content_elem.name == 'img':
                                        content = content_elem.get('alt', '')
                                    else:
                                        content = content_elem.text.strip()

                                # Get additional info
                                info = ''
                                info_elem = result.find('div', class_=['_2WrB', 'pod-info'])
                                if info_elem:
                                    info = info_elem.text.strip()

                                results.append({
                                    'type': 'website',
                                    'title': f"Wolfram Alpha: {title}",
                                    'url': url,
                                    'description': f"{content}\n{info}",
                                    'favicon': "https://www.wolframalpha.com/favicon.ico",
                                    'platform': 'Wolfram Alpha',
                                    'source': self._get_source_from_url(url)
                                })

                            except Exception as e:
                                logger.error(f"Error processing Wolfram Alpha result: {str(e)}")
                                continue

        except Exception as e:
            logger.error(f"Error searching Wolfram Alpha: {str(e)}")

        return results[:100]

    async def _search_archive(self, query: str) -> List[Dict]:
        """Search for historical content using Internet Archive."""
        results = []
        try:
            search_url = f"https://archive.org/search?query={quote(query)}"
            logger.info(f"Searching Internet Archive: {search_url}")

            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')

                        # Find search results
                        search_results = soup.find_all(['div', 'article'], class_=['item-ia', 'result-item'])
                        logger.info(f"Found {len(search_results)} archive results from Internet Archive")

                        for result in search_results:
                            try:
                                # Get title and URL
                                title_elem = result.find(['div', 'h3'], class_=['ttl', 'title-link'])
                                if not title_elem:
                                    continue

                                title = title_elem.text.strip()
                                link = result.find('a', class_=['stealth', 'item-link'])
                                url = f"https://archive.org{link.get('href', '')}" if link else ''

                                # Skip if no valid URL
                                if not url.startswith('http'):
                                    continue

                                # Get description and metadata
                                description = ''
                                desc_elem = result.find(['div', 'span'], class_=['item-description', 'description'])
                                if desc_elem:
                                    description = desc_elem.text.strip()

                                # Get additional metadata
                                metadata = []
                                meta_elems = result.find_all(['div', 'span'], class_=['item-details', 'metadata'])
                                for elem in meta_elems:
                                    metadata.append(elem.text.strip())

                                results.append({
                                    'type': 'website',
                                    'title': title,
                                    'url': url,
                                    'description': f"{description}\n{' | '.join(metadata)}",
                                    'favicon': "https://archive.org/favicon.ico",
                                    'platform': 'Internet Archive',
                                    'source': self._get_source_from_url(url)
                                })

                            except Exception as e:
                                logger.error(f"Error processing Internet Archive result: {str(e)}")
                                continue

        except Exception as e:
            logger.error(f"Error searching Internet Archive: {str(e)}")

        return results[:100]

    async def _search_metager(self, query: str) -> List[Dict]:
        """Search using MetaGer, a privacy-focused meta search engine."""
        results = []
        try:
            search_url = f"https://metager.org/meta/meta.ger3?eingabe={quote(query)}"
            logger.info(f"Searching MetaGer: {search_url}")

            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')

                        # Find search results
                        search_results = soup.find_all(['div', 'article'], class_=['result', 'web-result'])
                        logger.info(f"Found {len(search_results)} results from MetaGer")

                        for result in search_results:
                            try:
                                # Get title and URL
                                title_elem = result.find(['h2', 'a'], class_=['result-title', 'title'])
                                if not title_elem:
                                    continue

                                title = title_elem.text.strip()
                                url = title_elem.get('href', '')

                                # Skip if no valid URL
                                if not url.startswith('http'):
                                    continue

                                # Get description
                                description = ''
                                desc_elem = result.find(['p', 'div'], class_=['result-description', 'description'])
                                if desc_elem:
                                    description = desc_elem.text.strip()

                                # Get source info
                                source = ''
                                source_elem = result.find(['span', 'div'], class_=['result-host', 'source'])
                                if source_elem:
                                    source = source_elem.text.strip()

                                # Get favicon
                                parsed_url = urlparse(url)
                                favicon = f"https://www.google.com/s2/favicons?domain={quote(parsed_url.netloc)}"

                                results.append({
                                    'type': 'website',
                                    'title': title,
                                    'url': url,
                                    'description': f"{description}\nSource: {source}",
                                    'favicon': favicon,
                                    'platform': 'MetaGer',
                                    'source': self._get_source_from_url(url)
                                })

                            except Exception as e:
                                logger.error(f"Error processing MetaGer result: {str(e)}")
                                continue

        except Exception as e:
            logger.error(f"Error searching MetaGer: {str(e)}")

        return results[:100]

    async def _search_google_cse(self, query: str, cx: str) -> List[Dict]:
        """Search using Google Custom Search Engine."""
        results = []
        try:
            search_url = f"https://cse.google.com/cse?cx={cx}&q={quote(query)}"
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        for result in soup.find_all('div', class_='gsc-result'):
                            try:
                                # Get title and URL
                                title_elem = result.find('div', class_='gs-title')
                                if not title_elem:
                                    continue
                                    
                                link = title_elem.find('a', class_='gs-title')
                                if not link:
                                    continue
                                    
                                url = link.get('href', '')
                                if not url or not url.startswith('http'):
                                    continue
                                    
                                # Get description
                                description = ''
                                desc_elem = result.find('div', class_='gs-snippet')
                                if desc_elem:
                                    description = desc_elem.text.strip()
                                
                                # Get source from URL
                                source = self._get_source_from_url(url)
                                
                                # Get favicon
                                parsed_url = urlparse(url)
                                favicon = f"https://www.google.com/s2/favicons?domain={parsed_url.netloc}"
                                
                                results.append({
                                    'type': 'website',
                                    'title': title_elem.text.strip(),
                                    'url': url,
                                    'description': description,
                                    'favicon': favicon,
                                    'source': source,
                                    'platform': 'Google CSE'
                                })

                            except Exception as e:
                                logger.error(f"Error processing Google CSE result: {str(e)}")
                                continue

        except Exception as e:
            logger.error(f"Error searching Google CSE: {str(e)}")

        return results[:100]

    async def search_videos(self, session, query):
        logger.debug('Searching videos for query: %s', query)
        google_video_url = 'https://www.google.com/videohp'
        async with session.get(google_video_url, headers=self.headers) as response:
            if response.status == 200:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                # Find video elements
                video_elements = soup.find_all('div', class_='g')
                logger.info(f"Found {len(video_elements)} video elements")
                results = []
                for element in video_elements:
                    try:
                        # Get title and URL
                        title_elem = element.find('h3')
                        link = element.find('a')
                        if not title_elem or not link:
                            continue

                        title = title_elem.text.strip()
                        url = link.get('href', '')

                        # Skip if no valid URL
                        if not url.startswith('http'):
                            continue

                        # Get description
                        description = ''
                        desc_elem = element.find('div', class_='s')
                        if desc_elem:
                            description = desc_elem.text.strip()

                        # Get favicon
                        favicon = f"https://www.google.com/s2/favicons?domain={quote(url)}"

                        results.append({
                            'type': 'video',
                            'title': title,
                            'url': url,
                            'description': description,
                            'favicon': favicon,
                            'platform': 'Google',
                            'source': self._get_source_from_url(url)
                        })

                    except Exception as e:
                        logger.error(f"Error processing Google video result: {str(e)}")
                        continue
                return results
        return []

    async def _search_google_videos(self, query: str) -> List[Dict]:
        """Search for videos using Google Video Search."""
        results = []
        try:
            search_url = f"https://www.google.com/videohp?q={quote(query)}"
            logger.info(f"Searching Google Videos: {search_url}")

            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')

                        # Find search results
                        search_results = soup.find_all('div', class_='g')
                        logger.info(f"Found {len(search_results)} video results from Google")

                        for result in search_results:
                            try:
                                # Get title and URL
                                title_elem = result.find('h3')
                                link = result.find('a')
                                if not title_elem or not link:
                                    continue

                                title = title_elem.text.strip()
                                url = link.get('href', '')

                                # Skip if no valid URL
                                if not url.startswith('http'):
                                    continue

                                # Get description
                                description = ''
                                desc_elem = result.find('div', class_='s')
                                if desc_elem:
                                    description = desc_elem.text.strip()

                                # Get favicon
                                favicon = f"https://www.google.com/s2/favicons?domain={quote(url)}"

                                results.append({
                                    'type': 'video',
                                    'title': title,
                                    'url': url,
                                    'description': description,
                                    'favicon': favicon,
                                    'platform': 'Google Videos',
                                    'source': self._get_source_from_url(url)
                                })

                            except Exception as e:
                                logger.error(f"Error processing Google video result: {str(e)}")
                                continue

        except Exception as e:
            logger.error(f"Error searching Google Videos: {str(e)}")

        return results[:100]

def setup_routes(app, socketio):
    """Set up Flask routes and Socket.IO event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        logger.info('Client connected')
        emit('connect', {'message': 'Connected to server'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info('Client disconnected')
    
    @socketio.on('search_query')
    def handle_search(data):
        """Handle search request from client"""
        try:
            query = data.get('query', '').strip()
            search_types = data.get('searchTypes', {'videos': True, 'websites': True})
            
            if not query:
                emit('search_error', {'message': 'Please enter a search query'})
                return
                
            if not any(search_types.values()):
                emit('search_error', {'message': 'Please select at least one search type'})
                return
            
            # Notify client that search has started
            emit('search_started', {'message': f'Starting search for: {query}'})
            
            # Create crawler and run search
            try:
                crawler = VideoSearchCrawler(query)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                all_results = loop.run_until_complete(crawler.collect_results(search_types))
                loop.close()
                
                # Process and emit results
                processed_results = []
                for result in all_results:
                    processed_result = {
                        'url': result.get('url', ''),
                        'title': result.get('title', 'Untitled Result'),
                        'platform': result.get('platform', 'Unknown'),
                        'description': result.get('description', ''),
                        'thumbnail': result.get('thumbnail', '') or result.get('favicon', ''),
                        'source': result.get('source', 'Unknown'),
                        'duration': result.get('duration', 'Unknown'),
                        'type': result.get('type', 'Unknown')
                    }
                    processed_results.append(processed_result)
                    # Emit each result as it's processed
                    emit('new_result', {'result': processed_result, 'query': query})
                    
                # Notify client that search is complete
                emit('search_completed', {
                    'message': f'Search completed. Found {len(processed_results)} results.',
                    'total': len(processed_results)
                })
                
            except Exception as e:
                logger.error(f"Error in search: {str(e)}")
                emit('search_error', {'message': f'Error during search: {str(e)}'})
                
        except Exception as e:
            logger.error(f"Error handling search request: {str(e)}")
            emit('search_error', {'message': f'Error processing search request: {str(e)}'})

async def perform_search(query, search_type):
    results = []
    tasks = []
    
    async with aiohttp.ClientSession() as session:
        if search_type in ['all', 'videos']:
            tasks.append(search_videos(session, query))
        if search_type in ['all', 'websites']:
            tasks.append(search_websites(session, query))
        
        all_results = await asyncio.gather(*tasks)
        for result_set in all_results:
            results.extend(result_set)
    
    return results

async def search_videos(session, query):
    results = []
    try:
        # YouTube search
        search_url = f"https://www.youtube.com/results?search_query={query}"
        async with session.get(search_url) as response:
            html = await response.text()
            
        soup = BeautifulSoup(html, 'html.parser')
        video_elements = soup.find_all('div', {'class': 'yt-lockup-content'})
        
        for element in video_elements[:5]:  # Limit to first 5 results
            title_elem = element.find('a', {'class': 'yt-uix-tile-link'})
            if title_elem:
                video_id = title_elem['href'].split('=')[-1]
                title = title_elem.text
                
                results.append({
                    'type': 'video',
                    'title': title,
                    'url': f'https://www.youtube.com/watch?v={video_id}',
                    'embed_url': f'https://www.youtube.com/embed/{video_id}',
                    'thumbnail': f'https://img.youtube.com/vi/{video_id}/mqdefault.jpg'
                })
    except Exception as e:
        logger.error(f"Error searching videos: {str(e)}")
    
    return results

async def search_websites(session, query):
    results = []
    try:
        # Use DuckDuckGo for web search
        search_url = f"https://html.duckduckgo.com/html/?q={query}"
        async with session.get(search_url) as response:
            html = await response.text()
        
        soup = BeautifulSoup(html, 'html.parser')
        links = soup.find_all('div', {'class': 'result'})
        
        h = html2text.HTML2Text()
        h.ignore_links = True
        h.ignore_images = True
        
        for link in links[:5]:  # Limit to first 5 results
            title_elem = link.find('a', {'class': 'result__a'})
            snippet_elem = link.find('a', {'class': 'result__snippet'})
            
            if title_elem and snippet_elem:
                title = title_elem.text.strip()
                url = title_elem['href']
                description = h.handle(snippet_elem.text).strip()
                
                results.append({
                    'type': 'website',
                    'title': title,
                    'url': url,
                    'description': description
                })
    except Exception as e:
        logger.error(f"Error searching websites: {str(e)}")
    
    return results