import os
import sys
import logging
from pathlib import Path
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add the scrape directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
scrape_dir = os.path.join(current_dir, 'scrape')
if scrape_dir not in sys.path:
    sys.path.append(scrape_dir)

from flask import Flask, send_from_directory, send_file
from flask_cors import CORS
from flask_socketio import SocketIO
from scrape_upgrade import setup_routes

# When frozen by PyInstaller, the path to the resources is different
if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
    logger.info(f"Running in PyInstaller bundle. Base dir: {base_dir}")
else:
    base_dir = current_dir
    logger.info(f"Running in development mode. Base dir: {base_dir}")

static_folder = os.path.join(base_dir, 'public')
logger.info(f"Static folder path: {static_folder}")

# Initialize Flask app
app = Flask(__name__, 
           static_folder='public',
           static_url_path='')

# Configure CORS properly
CORS(app, resources={
    r"/*": {
        "origins": [
            "http://127.0.0.1:5001",
            "https://browser-client-server.vercel.app",
            "*"  # Allow all origins in development
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    }
})

# Initialize SocketIO with proper configuration
socketio = SocketIO(
    app,
    cors_allowed_origins=[
        "http://127.0.0.1:5001",
        "https://browser-client-server.vercel.app",
        "*"  # Allow all origins in development
    ],
    async_mode='threading',
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25,
    manage_session=False,
    always_connect=True
)

# Initialize data storage
try:
    # File to store websites and tags
    DATA_FILE = Path(current_dir) / 'data' / 'websites_tags.json'
    DATA_FILE.parent.mkdir(exist_ok=True)
    
    # Initialize empty data structures
    websites_tags = {}
    tag_frequencies = {}
    
    # Load existing data
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            websites_tags = data.get('websites_tags', {})
            tag_frequencies = data.get('tag_frequencies', {})
except Exception as e:
    logger.error(f"Error initializing data storage: {str(e)}", exc_info=True)
    websites_tags = {}
    tag_frequencies = {}

def save_data():
    try:
        DATA_FILE.parent.mkdir(exist_ok=True)
        with open(DATA_FILE, 'w') as f:
            json.dump({
                'websites_tags': websites_tags,
                'tag_frequencies': tag_frequencies
            }, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving data: {str(e)}", exc_info=True)

@socketio.on('submit_website_and_tags')
def handle_website_tags(data):
    try:
        website = data.get('website')
        tags = data.get('tags', [])
        
        if not website or not tags:
            return
        
        # Store website and its tags
        websites_tags[website] = tags
        
        # Update tag frequencies
        for tag in tags:
            tag_frequencies[tag] = tag_frequencies.get(tag, 0) + 1
        
        # Save to file
        save_data()
        
        # Emit updated tag frequencies to all clients
        socketio.emit('tag_frequencies_updated', {'frequencies': tag_frequencies})
    except Exception as e:
        logger.error(f"Error in handle_website_tags: {str(e)}", exc_info=True)
        socketio.emit('error', {'message': str(e)})

@socketio.on('search_query')
def handle_search(data):
    try:
        query = data.get('query', '')
        selected_tags = set(data.get('tags', []))
        
        # Get matching websites based on tags
        matching_websites = set()
        if selected_tags:
            for website, tags in websites_tags.items():
                if any(tag in selected_tags for tag in tags):
                    matching_websites.add(website)
        
        # Perform the search with the original query
        search_results = perform_search(query)
        
        # Filter results if we have matching websites
        if matching_websites:
            filtered_results = []
            for result in search_results:
                url = result.get('url')
                # Check if the URL is in our tagged websites
                if url in matching_websites:
                    result['tags'] = websites_tags[url]
                    filtered_results.append(result)
                # Also include URLs from the search that match our tagged websites
                elif any(tagged_url in url or url in tagged_url for tagged_url in matching_websites):
                    matching_url = next(tagged_url for tagged_url in matching_websites 
                                     if tagged_url in url or url in tagged_url)
                    result['tags'] = websites_tags[matching_url]
                    filtered_results.append(result)
            search_results = filtered_results
        
        # Add tags to results even if no tags were selected
        for result in search_results:
            url = result.get('url')
            # Try to find matching URL in our tagged websites
            matching_url = next((tagged_url for tagged_url in websites_tags 
                               if tagged_url in url or url in tagged_url), None)
            if matching_url:
                result['tags'] = websites_tags[matching_url]
        
        # Send results to client
        for result in search_results:
            socketio.emit('search_results', {'result': result})
        
        # Get recommended tags based on the query
        recommended_tags = get_recommended_tags(query)
        socketio.emit('recommended_tags', {'tags': recommended_tags})
        
    except Exception as e:
        logger.error(f"Error in handle_search: {str(e)}", exc_info=True)
        socketio.emit('error', {'message': str(e)})
    finally:
        socketio.emit('search_complete')

def get_recommended_tags(query):
    # Get tags that are semantically related to the query
    recommended = []
    query_words = set(query.lower().split())
    
    for tag, frequency in tag_frequencies.items():
        tag_words = set(tag.lower().split())
        # Check for word overlap or if tag is substring of query or vice versa
        if (query_words & tag_words or 
            tag.lower() in query.lower() or 
            query.lower() in tag.lower()):
            recommended.append({
                'tag': tag,
                'frequency': frequency
            })
    
    # Sort by frequency and return top 10
    recommended.sort(key=lambda x: x['frequency'], reverse=True)
    return [item['tag'] for item in recommended[:10]]

@app.route('/')
def index():
    try:
        return send_from_directory('public', 'index.html')
    except Exception as e:
        logger.error(f"Error serving index.html: {str(e)}", exc_info=True)
        return f"Error: {str(e)}", 500

@app.route('/<path:path>')
def serve_static(path):
    try:
        return send_from_directory('public', path)
    except Exception as e:
        logger.error(f"Error serving static file {path}: {str(e)}", exc_info=True)
        return f"Error: {str(e)}", 500

# Set up all routes and socket handlers
setup_routes(app, socketio)

if __name__ == '__main__':
    try:
        # Check if running on Vercel
        if os.environ.get('VERCEL'):
            app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5001)))
        else:
            logger.info("Starting Flask-SocketIO server...")
            socketio.run(
                app,
                host='0.0.0.0',
                port=5001,
                debug=True,
                allow_unsafe_werkzeug=True,
                use_reloader=False,  # Disable reloader to avoid duplicate connections
                log_output=True
            )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}", exc_info=True)
        raise  # Re-raise the exception to see the full error
