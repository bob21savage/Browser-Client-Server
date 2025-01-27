# Multi-Platform Video Scraper

An advanced web application that searches and aggregates videos from multiple platforms including YouTube, Vimeo, and Dailymotion. Features browser rotation and anti-detection measures.

## Features

- Multi-platform video search (YouTube, Vimeo, Dailymotion)
- Asynchronous scraping for better performance
- Browser rotation to avoid detection
- Modern, responsive UI with dark mode support
- Platform filtering
- Embedded video players

## Installation

### Option 1: Basic Installation

1. Make sure you have Python 3.8+ installed

2. Clone this repository:
```bash
git clone <your-repo-url>
cd scrape
```

3. Create a virtual environment (recommended):
```bash
python -m venv venv
```

4. Activate the virtual environment:
- Windows:
```bash
venv\Scripts\activate
```
- Linux/Mac:
```bash
source venv/bin/activate
```

5. Install requirements:
```bash
pip install -r requirements.txt
```

### Option 2: Development Installation

For development or contributing to the project:

1. Follow steps 1-4 from Option 1

2. Install in development mode:
```bash
pip install -e .
```

3. Install with development dependencies (includes testing and linting tools):
```bash
pip install -e .[dev]
```
4. Install as a package:
```bash
npx pkg .
```
6. Build and run the package:
```bash
npm run package-win
```
### Option 3: Package Installation

To install directly as a package:

```bash
pip install advanced-scraper
```

## Usage

1. Start the server:
```bash
python ./app.py
```
2. Run the package:
```bash
node start server.cjs
```
3. run this to test the package:
```bash
npm run dev:all
```
4. then check the status of the package:
```
## Video Embedding

This project supports video embedding using the following libraries:

### Installation

Make sure to install the required packages:

```bash
pip install -r requirements.txt
```

### Usage

1. Run the Electron application:
```bash
& "c:/Users/bpier/Downloads/scrape/scrape/scrape/my app/scrape/node_modules/.bin/electron" "c:/Users/bpier/Downloads/scrape/scrape/scrape/my app/scrape/server.cjs"
```
## Building and Serving the React Application

To build and serve the React application, follow these steps:

1. Build the React application:
   ```bash
   npm run build
   ```

2. Install the `serve` package globally:
   ```bash
   npm install -g serve
   ```

3. Serve the built application:
   ```bash
   serve -s build
   ```
## Running the Application

### For Windows Users
1. Double-click `WindowsServer.bat` to install dependencies, build, and serve the application.

### For macOS/Linux Users
1. Open a terminal.
2. Navigate to the project directory.
3. Run `chmod +x MacOSLinuxSever.sh` to make the script executable.
4. Execute the script with `./MacOSLinuxSever.sh`.

## Troubleshooting

If you encounter SSL certificate errors while installing packages:
```bash

```

If you get browser driver errors:
1. Make sure you have Chrome, Firefox, or Edge installed
2. The webdriver-manager should automatically download the appropriate driver

## Requirements

- Python 3.8+
- Modern web browser (Chrome, Firefox, or Edge)
- Internet connection

## Dependencies

- quart
- aiohttp
- asyncio
- bs4 (BeautifulSoup)
- requests
- requests_html
- lxml
- urllib3
- chardet
- certifi
- idna
- python_anticaptcha
- robotexclusionrulesparser
- python_dotenv
- dotenv
- brotli
- hypercorn
- hypercorn.asyncio
- wsproto
- h11
- priority
- toml
- typing_extensions
- html5lib
- flask
- flask_socketio

## Electron App Setup

### Ensure the UI Loads

1. Make sure the HTML file (e.g., `index.html`) exists in the `templates` directory.
2. The server should load the HTML file with the following line:
   ```javascript
   res.sendFile(__dirname + '/templates/index.html');
   ```
3. Open the developer tools in the Electron app to check for any errors in the console.
4. Verify that the server is running without errors and listening on the correct port.

## Note

This scraper is for educational purposes only. Please respect the terms of service and robot.txt files of the platforms you're scraping.