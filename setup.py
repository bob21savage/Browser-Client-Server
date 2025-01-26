"""Legacy setup.py for backward compatibility"""
from setuptools import setup, find_packages

# This setup.py is maintained for backward compatibility
# Prefer using pyproject.toml for new installations
setup(
    name="video-link-scraper",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "flask>=2.0.0",
        "flask-socketio>=5.3.0",
        "flask-cors>=4.0.0",
        "gevent>=24.11.1",
        "gevent-websocket>=0.10.1",
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "python-engineio>=4.8.0",
        "python-socketio>=5.10.0",
        "zope.event>=5.0",
        "zope.interface>=7.2",
        "greenlet>=3.1.1",
    ],
    python_requires=">=3.8",
    author="Your Name",
    author_email="your.email@example.com",
    description="A real-time video link scraper with WebSocket support",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/video-link-scraper",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
