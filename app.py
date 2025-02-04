import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add the scrape directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
scrape_dir = os.path.join(current_dir, 'scrape')
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

app = Flask(__name__, 
           static_folder=static_folder,
           static_url_path='')

# Configure CORS
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    }
})

# Initialize SocketIO with minimal configuration
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    logger=True,
    engineio_logger=True
)

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

# Set up all routes and socket handlers
setup_routes(app, socketio)

if __name__ == '__main__':
    logger.info("Starting Flask-SocketIO server...")
    port = int(os.environ.get('PORT', 5001))
    logger.info(f"Server will run on port {port}")
    socketio.run(
        app,
        host='127.0.0.1',
        port=port,
        debug=True,
        use_reloader=False
    )
