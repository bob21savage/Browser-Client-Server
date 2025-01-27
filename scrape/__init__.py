"""Video Link Scraper Package"""

__version__ = "0.1.0"

# Remove the import for app to prevent circular imports
# from .scrape_upgrade import app, socketio
from .scrape_upgrade import socketio  # Keep this if socketio is used
