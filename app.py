import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add the scrape directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
scrape_dir = os.path.join(current_dir, 'scrape')
if scrape_dir not in sys.path:
    sys.path.append(scrape_dir)

from flask import Flask, send_from_directory, send_file, request
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

# Configure CORS
CORS(app, resources={
    r"/*": {
        "origins": ["https://browser-client-server.vercel.app", "http://127.0.0.1:5001"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    }
})

# Initialize SocketIO
socketio = SocketIO(
    app,
    cors_allowed_origins=["https://browser-client-server.vercel.app", "http://127.0.0.1:5001"],
    async_mode='threading',
    logger=True,
    engineio_logger=True,
    ping_timeout=60000,
    ping_interval=25000,
    manage_session=False,
    always_connect=True,
    transports=['polling']
)

@app.route('/')
def index():
    try:
        logger.info("Serving index.html")
        return send_from_directory('public', 'index.html')
    except Exception as e:
        logger.error(f"Error serving index.html: {str(e)}")
        return f"Error: {str(e)}", 500

@app.route('/<path:path>')
def serve_static(path):
    try:
        logger.info(f"Serving static file: {path}")
        return send_from_directory('public', path)
    except Exception as e:
        logger.error(f"Error serving static file {path}: {str(e)}")
        return f"Error: {str(e)}", 500

# Socket.IO connection handlers
@socketio.on('connect')
def handle_connect():
    logger.info(f"Client connected from {request.remote_addr}")
    socketio.emit('connect_response', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"Client disconnected from {request.remote_addr}")

# Set up all routes and socket handlers
setup_routes(app, socketio)

if __name__ == '__main__':
    try:
        if os.environ.get('VERCEL'):
            # Running on Vercel
            logger.info("Starting server in Vercel environment")
            app.run(
                host='0.0.0.0',
                port=int(os.environ.get('PORT', 5001)),
                debug=False
            )
        else:
            # Local development
            logger.info("Starting Flask-SocketIO server in development mode")
            socketio.run(
                app,
                host='127.0.0.1',
                port=5001,
                debug=True,
                allow_unsafe_werkzeug=True,
                use_reloader=False
            )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
