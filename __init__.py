"""Video Link Scraper Package"""

__version__ = "0.1.0"

from .scrape_upgrade import VideoSearchCrawler

# Function to set search queries dynamically
search_queries = []

def set_search_queries(queries):
    global search_queries
    search_queries = queries

# Get search queries from user input
user_input = input("Enter search queries separated by commas: ")
search_queries = [query.strip() for query in user_input.split(",")]

# Implementing User-Agent rotation
import random
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Gecko/20100101 Firefox/60.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/17.17134'
]

# Function to get a random User-Agent
import requests

def get_random_user_agent():
    return random.choice(user_agents)

# Adding error handling and retries
import time

def scrape_with_retries(url, retries=3):
    for i in range(retries):
        try:
            headers = {'User-Agent': get_random_user_agent()}
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise an error for bad responses
            return response
        except requests.exceptions.RequestException as e:
            print(f'Error: {e}. Retrying...')
            time.sleep(2)  # Delay before retrying
    return None

# Example usage of the new scraping function
for query in search_queries:
    url = f'https://www.bing.com/search?q={query}'
    response = scrape_with_retries(url)
    if response:
        # Process the response
        pass
    else:
        print('Failed to retrieve data after retries.')

# Introduce a delay between requests
import time

def delay_between_requests(seconds):
    time.sleep(seconds)

# Example of using the delay function
for query in search_queries:
    url = f'https://www.bing.com/search?q={query}'
    response = scrape_with_retries(url)
    if response:
        # Process the response
        pass
    delay_between_requests(5)  # Delay for 5 seconds

# Additional imports for HTML parsing
from bs4 import BeautifulSoup

# Method to collect YouTube links
def collect_youtube_links(search_query):
    youtube_links = []
    youtube_url = f'https://www.youtube.com/results?search_query={search_query}'
    response = scrape_with_retries(youtube_url)
    if response:
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a'):
            href = link.get('href')
            if '/watch?v=' in href:
                full_link = f'https://www.youtube.com{href}'
                youtube_links.append(full_link)
    return youtube_links

# Method to collect other links
def collect_other_links(search_query):
    other_links = []
    url = f'https://www.bing.com/search?q={search_query}'
    response = scrape_with_retries(url)
    if response:
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and href.startswith('http'):
                other_links.append(href)
    return other_links

# Method to collect DuckDuckGo links
def collect_duckduckgo_links(search_query):
    duckduckgo_links = []
    url = f'https://duckduckgo.com/?q={search_query}'
    response = scrape_with_retries(url)
    if response:
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and href.startswith('http'):
                duckduckgo_links.append(href)
    return duckduckgo_links

# Method to collect Yahoo links
def collect_yahoo_links(search_query):
    yahoo_links = []
    url = f'https://search.yahoo.com/search?p={search_query}'
    response = scrape_with_retries(url)
    if response:
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and href.startswith('http'):
                yahoo_links.append(href)
    return yahoo_links

# Method to collect GitHub repositories
def collect_github_links(search_query):
    github_links = []
    url = f'https://github.com/search?q={search_query}'
    response = scrape_with_retries(url)
    if response:
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and '/repos/' in href:
                full_link = f'https://github.com{href}'
                github_links.append(full_link)
    return github_links

# Method to collect links from Archive.org
def collect_archive_links(search_query):
    archive_links = []
    url = f'https://archive.org/search.php?query={search_query}'
    response = scrape_with_retries(url)
    if response:
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and 'archive.org' in href:
                full_link = f'https://archive.org{href}'
                archive_links.append(full_link)
    return archive_links

# Method to collect Semantic Scholar papers
def collect_semantic_scholar_links(search_query):
    semantic_links = []
    url = f'https://www.semanticscholar.org/search?q={search_query}'
    response = scrape_with_retries(url)
    if response:
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and 'semanticscholar.org' in href:
                full_link = f'https://www.semanticscholar.org{href}'
                semantic_links.append(full_link)
    return semantic_links

# Method to collect BASE resources
def collect_base_links(search_query):
    base_links = []
    url = f'https://www.base-search.net/Search/Results?lookfor={search_query}'
    response = scrape_with_retries(url)
    if response:
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and 'base-search.net' in href:
                full_link = f'https://www.base-search.net{href}'
                base_links.append(full_link)
    return base_links

# Method to collect YouTube mobile links
def collect_youtube_mobile_links(search_query):
    youtube_links = []
    youtube_mobile_url = f'https://m.youtube.com/results?search_query={search_query}'
    response = scrape_with_retries(youtube_mobile_url)
    if response:
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a'):
            href = link.get('href')
            if '/watch?v=' in href:
                full_link = f'https://www.youtube.com{href}'
                youtube_links.append(full_link)
    return youtube_links

# Method to collect computational results from Wolfram Alpha
def collect_wolfram_alpha_links(search_query):
    wolfram_links = []
    url = f'https://www.wolframalpha.com/input/?i={search_query}'
    response = scrape_with_retries(url)
    if response:
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and 'wolframalpha.com' in href:
                full_link = f'https://www.wolframalpha.com{href}'
                wolfram_links.append(full_link)
    return wolfram_links

# Method to collect Google search results
def collect_google_links(search_query):
    google_links = []
    url = f'https://www.google.com/search?q={search_query}'
    response = scrape_with_retries(url)
    if response:
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and 'url?q=' in href:
                full_link = href.split('url?q=')[1].split('&')[0]
                google_links.append(full_link)
    return google_links

# Method to collect MetaGer search results
def collect_metager_links(search_query):
    metager_links = []
    url = f'https://metager.de/meta/meta.ger?q={search_query}'
    response = scrape_with_retries(url)
    if response:
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and 'metager.de' in href:
                metager_links.append(href)
    return metager_links

# Method to collect arXiv papers
def collect_arxiv_links(search_query):
    arxiv_links = []
    url = f'https://arxiv.org/search/?query={search_query}&searchtype=all&source=header'
    response = scrape_with_retries(url)
    if response:
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and '/abs/' in href:
                full_link = f'https://arxiv.org{href}'
                arxiv_links.append(full_link)
    return arxiv_links

# Method to collect Qwant search results
def collect_qwant_links(search_query):
    qwant_links = []
    url = f'https://www.qwant.com/?q={search_query}'
    response = scrape_with_retries(url)
    if response:
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and 'qwant.com' in href:
                qwant_links.append(href)
    return qwant_links

# Function to fetch results from the YouTube JavaScript link
def fetch_youtube_and_search_results(query):
    import requests
    # Fetch results from the provided JavaScript link
    js_url = 'https://www.youtube.com/s/player/b0557ce3/player_ias.vflset/en_US/base.js'
    response = requests.get(js_url)
    if response.status_code == 200:
        # Process the JavaScript response to extract relevant data
        # This is a placeholder for processing logic, adjust as necessary
        return response.text  # Return the JavaScript content or processed data
    else:
        return None

# Method to fetch YouTube search results
def fetch_youtube_search_results(query, api_key):
    import requests
    url = f'https://www.googleapis.com/youtube/v3/search?part=id&q={query}&key={api_key}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()['items']  # Return the JSON content of the YouTube search results
    else:
        return None

# Method to fetch YouTube video IDs and generate HTML code to embed those videos
def generate_youtube_embed_code(query, api_key):
    # Fetch YouTube search results
    results = fetch_youtube_search_results(query, api_key)
    embed_code = ''
    for item in results:
        video_id = item['id']['videoId']  # Extract video ID
        embed_code += f'<iframe width="560" height="315" src="https://www.youtube.com/embed/{video_id}" frameborder="0" allowfullscreen></iframe>\n'
    return embed_code

# Method to perform a combined search
def combined_search(query):
    search_results = collect_other_links(query)  # Collect from other links
    youtube_results = fetch_youtube_and_search_results(query)  # Fetch results from the JavaScript link
    combined_results = []
    if youtube_results:
        combined_results.append(youtube_results)
    combined_results.extend(search_results)  # Combine both results
    return combined_results

# Method to combine YouTube Data API results with search engine results
def combined_search_with_youtube(query, api_key):
    # Collect links from other search engines
    search_engine_results = collect_other_links(query)
    
    # Fetch YouTube search results
    youtube_results = fetch_youtube_search_results(query, api_key)
    
    # Extract YouTube video links
    youtube_links = [f'https://www.youtube.com/watch?v={item["id"]["videoId"]}' for item in youtube_results]
    
    # Combine results
    combined_results = {
        'search_engine_results': search_engine_results,
        'youtube_links': youtube_links
    }
    
    return combined_results

# Load environment variables from .env file
from dotenv import load_dotenv
import os
load_dotenv()
api_key = os.getenv('YOUTUBE_API_KEY')  # Get the API key from environment variables

# Example usage of collecting YouTube links and other links
for query in search_queries:
    youtube_links = collect_youtube_links(query)
    other_links = collect_other_links(query)
    duckduckgo_links = collect_duckduckgo_links(query)
    yahoo_links = collect_yahoo_links(query)
    github_links = collect_github_links(query)
    archive_links = collect_archive_links(query)
    semantic_links = collect_semantic_scholar_links(query)
    base_links = collect_base_links(query)
    youtube_mobile_links = collect_youtube_mobile_links(query)
    wolfram_links = collect_wolfram_alpha_links(query)
    google_links = collect_google_links(query)
    metager_links = collect_metager_links(query)
    arxiv_links = collect_arxiv_links(query)
    qwant_links = collect_qwant_links(query)
    print(f'YouTube links for query "{query}": {youtube_links}')
    print(f'Other links for query "{query}": {other_links}')
    print(f'DuckDuckGo links for query "{query}": {duckduckgo_links}')
    print(f'Yahoo links for query "{query}": {yahoo_links}')
    print(f'GitHub links for query "{query}": {github_links}')
    print(f'Archive.org links for query "{query}": {archive_links}')
    print(f'Semantic Scholar links for query "{query}": {semantic_links}')
    print(f'BASE links for query "{query}": {base_links}')
    print(f'YouTube mobile links for query "{query}": {youtube_mobile_links}')
    print(f'Wolfram Alpha links for query "{query}": {wolfram_links}')
    print(f'Google links for query "{query}": {google_links}')
    print(f'MetaGer links for query "{query}": {metager_links}')
    print(f'arXiv links for query "{query}": {arxiv_links}')
    print(f'Qwant links for query "{query}": {qwant_links}')

# Example usage of generating YouTube embed code
for query in search_queries:
    embed_code = generate_youtube_embed_code(query, api_key)
    print(f'YouTube embed code for query "{query}": {embed_code}')

# Example usage of combined search with YouTube
for query in search_queries:
    combined_results = combined_search_with_youtube(query, api_key)
    print(f'Combined search results for query "{query}": {combined_results}')
