import os
import sys
import logging
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from flask_socketio import SocketIO
import asyncio

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add the scrape directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
scrape_dir = os.path.join(current_dir, 'scrape')
if scrape_dir not in sys.path:
    sys.path.append(scrape_dir)

# When frozen by PyInstaller, the path to the resources is different
if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
    logger.info(f"Running in PyInstaller bundle. Base dir: {base_dir}")
else:
    base_dir = current_dir
    logger.info(f"Running in development mode. Base dir: {base_dir}")

static_folder = os.path.join(base_dir, 'public')
logger.info(f"Static folder path: {static_folder}")

app = Flask(__name__, 
           static_folder=static_folder,
           static_url_path='')

# Configure CORS
CORS(app)

# Initialize SocketIO with proper configuration
socketio = SocketIO(app)

from scrape.scrape_upgrade import VideoSearchCrawler

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    query = data.get('query')

    if not query:
        return jsonify({'error': 'Query parameter is required.'}), 400

    try:
        crawler = VideoSearchCrawler(query)
        results = crawler.collect_results({'videos': True, 'websites': True})
        return jsonify(results)
    except Exception as e:
        print(f"Error during search: {str(e)}")  # Log the error
        return jsonify({'error': 'An error occurred during the search.'}), 500

@app.route('/')
def index():
    try:
        logger.info("Serving index.html")
        index_path = os.path.join(static_folder, 'index.html')
        logger.debug(f"Index path: {index_path}")
        if os.path.exists(index_path):
            return send_file(index_path)
        else:
            logger.error(f"index.html not found at {index_path}")
            return "Error: index.html not found", 404
    except Exception as e:
        logger.error(f"Error serving index.html: {str(e)}")
        return f"Error: {str(e)}", 500

@app.route('/<path:path>')
def serve_static(path):
    try:
        logger.info(f"Serving static file: {path}")
        file_path = os.path.join(static_folder, path)
        logger.debug(f"Full file path: {file_path}")
        if os.path.exists(file_path):
            return send_file(file_path)
        else:
            logger.error(f"File not found: {file_path}")
            return f"File not found: {path}", 404
    except Exception as e:
        logger.error(f"Error serving static file {path}: {str(e)}")
        return f"Error: {str(e)}", 500

@app.route('/favicon.ico')
def favicon():
    try:
        logger.info("Serving favicon.ico")
        return send_from_directory(static_folder, 'favicon.ico')
    except Exception as e:
        logger.error(f"Error serving favicon.ico: {str(e)}")
        return f"Error: {str(e)}", 500

# Set up all routes and socket handlers
from scrape.scrape_upgrade import setup_routes
setup_routes(app, socketio)

if __name__ == '__main__':
    logger.info("Starting Flask-SocketIO server...")
    app.run(host='0.0.0.0', port=5001, debug=True)  # No host or port specified for Vercel deployment
