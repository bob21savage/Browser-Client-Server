import os
import sys
import logging
from pathlib import Path
import asyncio

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
from flask_socketio import SocketIO, emit
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
            "https://browser-client-server.vercel.app"
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
        "https://browser-client-server.vercel.app"
    ],
    async_mode='eventlet',  # Use eventlet for async support
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25,
    always_connect=True,
    manage_session=False
)

@app.route('/')
async def index():
    try:
        logger.info("Serving index.html")
        index_path = os.path.join(static_folder, 'index.html')
        logger.debug(f"Index path: {index_path}")
        if os.path.exists(index_path):
            return await send_file(index_path)
        else:
            logger.error(f"index.html not found at {index_path}")
            return "Error: index.html not found", 404
    except Exception as e:
        logger.error(f"Error serving index.html: {str(e)}")
        return f"Error: {str(e)}", 500

@app.route('/<path:path>')
async def serve_static(path):
    try:
        logger.info(f"Serving static file: {path}")
        file_path = os.path.join(static_folder, path)
        logger.debug(f"Full file path: {file_path}")
        if os.path.exists(file_path):
            return await send_file(file_path)
        else:
            logger.error(f"File not found: {file_path}")
            return f"File not found: {path}", 404
    except Exception as e:
        logger.error(f"Error serving static file {path}: {str(e)}")
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
                host='127.0.0.1',
                port=5001,
                debug=True,
                allow_unsafe_werkzeug=True,
                use_reloader=False  # Disable reloader to avoid duplicate connections
            )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
