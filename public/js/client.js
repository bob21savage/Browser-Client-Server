// Get the server URL dynamically
const serverUrl = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://127.0.0.1:5001'
    : 'https://browser-client-server.vercel.app';

// Connect to Socket.IO server
const socket = io(serverUrl, {
    reconnection: true,
    reconnectionAttempts: Infinity,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    timeout: 20000,
    transports: ['websocket', 'polling'],
    path: '/socket.io/',
    forceNew: true
});

// DOM Elements
const searchForm = document.getElementById('search-form');
const searchInput = document.getElementById('search-input');
const searchButton = document.getElementById('search-button');
const searchVideos = document.getElementById('search-videos');
const searchWebsites = document.getElementById('search-websites');
const resultsContainer = document.getElementById('results');
const statusElement = document.getElementById('status');
const statsElement = document.getElementById('stats');

let totalResults = 0;
let videoResults = 0;
let websiteResults = 0;

let allResults = [];
let currentlyDisplayedResults = 0;
const resultsPerPage = 5;

// Socket.IO event handlers
socket.on('connect', () => {
    console.log('Connected to server');
    updateStatus('Connected to server', 'success');
    if (searchButton) searchButton.disabled = false;
});

socket.on('connect_error', (error) => {
    console.error('Connection error:', error);
    updateStatus('Connection error: ' + error.message, 'error');
});

socket.on('disconnect', (reason) => {
    console.log('Disconnected:', reason);
    updateStatus('Disconnected from server: ' + reason, 'error');
    if (searchButton) searchButton.disabled = true;
});

socket.on('search_started', (data) => {
    console.log('Search started:', data);
    updateStatus(data.message, 'info');
    clearResults();
    showLoadingIndicator();
    if (searchButton) searchButton.disabled = true;
    totalResults = 0;
    videoResults = 0;
    websiteResults = 0;
});

socket.on('new_result', (data) => {
    console.log('New result:', data);
    if (data.result) {
        totalResults++;
        if (data.result.type === 'video') {
            videoResults++;
        } else if (data.result.type === 'website') {
            websiteResults++;
        }
        allResults.push(data.result);
        if (allResults.length > currentlyDisplayedResults) {
            displayResults(allResults);
        }
        updateSearchStats({ 
            total: totalResults,
            videos: videoResults,
            websites: websiteResults,
            query: data.query
        });
    }
});

socket.on('search_completed', (data) => {
    console.log('Search completed:', data);
    hideLoadingIndicator();
    updateStatus(`Search completed. Found ${data.total} results.`, 'success');
    updateSearchStats(data);
    if (searchButton) searchButton.disabled = false;
});

socket.on('search_error', (data) => {
    console.error('Search error:', data);
    hideLoadingIndicator();
    updateStatus(`Error: ${data.error}`, 'error');
    if (searchButton) searchButton.disabled = false;
});

// Helper Functions
function updateStatus(message, type = 'info') {
    if (statusElement) {
        statusElement.textContent = message;
        statusElement.className = `status status-${type}`;
    }
}

function clearResults() {
    if (resultsContainer) resultsContainer.innerHTML = '';
    if (statsElement) statsElement.innerHTML = '';
    totalResults = 0;
    videoResults = 0;
    websiteResults = 0;
    allResults = [];
    currentlyDisplayedResults = 0;
}

function showLoadingIndicator() {
    if (!resultsContainer) return;
    const loader = document.createElement('div');
    loader.className = 'loader';
    loader.id = 'loader';
    resultsContainer.prepend(loader);
}

function hideLoadingIndicator() {
    const loader = document.getElementById('loader');
    if (loader) loader.remove();
}

function updateSearchStats(data) {
    if (!statsElement) return;
    statsElement.innerHTML = `
        <div class="search-stats">
            <span class="stat-item">Total Results: ${data.total || 0}</span>
            <span class="stat-item">Videos: ${data.videos || 0}</span>
            <span class="stat-item">Websites: ${data.websites || 0}</span>
            ${data.query ? `<span class="stat-item">Query: ${data.query}</span>` : ''}
        </div>
    `;
}

function displayResults(results) {
    const resultsContainer = document.getElementById('results');
    resultsContainer.innerHTML = ''; // Clear existing results
    allResults = results;
    currentlyDisplayedResults = 0;
    
    // Display first batch of results
    showMoreResults();
}

function showMoreResults() {
    const resultsContainer = document.getElementById('results');
    const endIndex = Math.min(currentlyDisplayedResults + resultsPerPage, allResults.length);
    
    // Display the next batch of results
    for (let i = currentlyDisplayedResults; i < endIndex; i++) {
        const result = allResults[i];
        const resultElement = createResultElement(result);
        resultsContainer.appendChild(resultElement);
    }
    
    // Update the counter
    currentlyDisplayedResults = endIndex;
    
    // Remove existing Show More button if any
    const existingButton = document.getElementById('show-more-btn');
    if (existingButton) {
        existingButton.remove();
    }
    
    // Add Show More button if there are more results
    if (currentlyDisplayedResults < allResults.length) {
        const showMoreButton = document.createElement('button');
        showMoreButton.id = 'show-more-btn';
        showMoreButton.className = 'show-more-button';
        showMoreButton.textContent = `Show More (${allResults.length - currentlyDisplayedResults} more results)`;
        showMoreButton.onclick = showMoreResults;
        resultsContainer.appendChild(showMoreButton);
    }
}

function createVideoEmbed(url) {
    if (!url) return '';
    
    console.log('Creating video embed for URL:', url);
    
    // YouTube URL patterns
    const youtubePatterns = [
        /(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([^&#]+)/i,
        /(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([^?&#]+)/i,
        /(?:https?:\/\/)?(?:www\.)?youtube\.com\/v\/([^?&#]+)/i,
        /(?:https?:\/\/)?(?:www\.)?youtu\.be\/([^?&#]+)/i
    ];
    
    // Vimeo URL patterns
    const vimeoPatterns = [
        /(?:https?:\/\/)?(?:www\.)?vimeo\.com\/(\d+)/i,
        /(?:https?:\/\/)?(?:www\.)?player\.vimeo\.com\/video\/(\d+)/i
    ];
    
    // Dailymotion URL patterns
    const dailymotionPatterns = [
        /(?:https?:\/\/)?(?:www\.)?dailymotion\.com(?:\/video|\/hub)\/([a-zA-Z0-9]+)/i,
        /(?:https?:\/\/)?(?:www\.)?dai\.ly\/([a-zA-Z0-9]+)/i
    ];

    // Check YouTube
    for (const pattern of youtubePatterns) {
        const match = url.match(pattern);
        if (match && match[1]) {
            console.log('Creating YouTube embed for:', match[1]);
            return `<iframe 
                src="https://www.youtube.com/embed/${match[1]}?autoplay=0&rel=0" 
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                allowfullscreen>
            </iframe>`;
        }
    }
    
    // Check Vimeo
    for (const pattern of vimeoPatterns) {
        const match = url.match(pattern);
        if (match && match[1]) {
            console.log('Creating Vimeo embed for:', match[1]);
            return `<iframe 
                src="https://player.vimeo.com/video/${match[1]}?autoplay=0" 
                allow="autoplay; fullscreen; picture-in-picture" 
                allowfullscreen>
            </iframe>`;
        }
    }
    
    // Check Dailymotion
    for (const pattern of dailymotionPatterns) {
        const match = url.match(pattern);
        if (match && match[1]) {
            console.log('Creating Dailymotion embed for:', match[1]);
            return `<iframe 
                src="https://www.dailymotion.com/embed/video/${match[1]}?autoplay=0" 
                allow="autoplay; fullscreen; picture-in-picture" 
                allowfullscreen>
            </iframe>`;
        }
    }
    
    console.log('No supported video platform found for URL:', url);
    return null;
}

function createResultElement(result) {
    const resultDiv = document.createElement('div');
    resultDiv.className = 'result';
    
    // Create favicon element
    const favicon = document.createElement('img');
    favicon.src = result.favicon || 'favicon.ico';
    favicon.className = 'favicon';
    favicon.onerror = () => { favicon.src = 'favicon.ico'; };
    
    // Create title with link
    const title = document.createElement('a');
    title.href = result.url;
    title.target = '_blank';
    title.className = 'result-title';
    title.textContent = result.title;
    
    // Create description
    const description = document.createElement('p');
    description.className = 'result-description';
    description.textContent = result.description;
    
    // Create source/platform info
    const source = document.createElement('span');
    source.className = 'result-source';
    source.textContent = `Source: ${result.source || result.platform || 'Unknown'}`;
    
    // Create video embed container (hidden by default)
    const videoContainer = document.createElement('div');
    videoContainer.className = 'video-container';
    videoContainer.style.display = 'none';
    
    // Add Watch Now button for video results
    if (result.type === 'video') {
        const watchButton = document.createElement('button');
        watchButton.className = 'watch-button';
        watchButton.innerHTML = '<i class="fas fa-play"></i> Watch Now';
        
        // Create video embed when button is clicked
        watchButton.onclick = (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            // Toggle video display
            if (videoContainer.style.display === 'none') {
                handleWatchClick(resultDiv, result.url);
            } else {
                videoContainer.style.display = 'none';
                videoContainer.innerHTML = '';
                watchButton.innerHTML = '<i class="fas fa-play"></i> Watch Now';
                console.log('Video embed closed');
            }
        };
        
        source.appendChild(watchButton);
    }
    
    // Assemble the result element
    const headerDiv = document.createElement('div');
    headerDiv.className = 'result-header';
    headerDiv.appendChild(favicon);
    headerDiv.appendChild(title);
    
    resultDiv.appendChild(headerDiv);
    resultDiv.appendChild(description);
    resultDiv.appendChild(source);
    resultDiv.appendChild(videoContainer);
    
    return resultDiv;
}

function handleWatchClick(resultElement, url) {
    const videoContainer = resultElement.querySelector('.video-container');
    if (!videoContainer) return;

    const embedHtml = createVideoEmbed(url);
    if (embedHtml) {
        videoContainer.innerHTML = embedHtml + '<button class="close-button" onclick="closeVideo(this)">Close Video</button>';
        videoContainer.style.display = 'block';
    } else {
        videoContainer.innerHTML = '<div class="error">Sorry, this video cannot be embedded.</div>';
        if (confirm('Would you like to watch this video on the original website?')) {
            window.open(url, '_blank');
        }
    }
}

function addSearchResult(result) {
    if (!resultsContainer || !result) return;
    
    const resultElement = document.createElement('div');
    resultElement.className = `result-item ${result.type}`;
    
    if (result.type === 'video') {
        // Add video embed or thumbnail
        const embedHtml = createVideoEmbed(result.url);
        if (embedHtml) {
            const embedContainer = document.createElement('div');
            embedContainer.className = 'video-embed';
            embedContainer.innerHTML = embedHtml;
            resultElement.appendChild(embedContainer);
        } else if (result.thumbnail) {
            const thumbnail = document.createElement('img');
            thumbnail.src = result.thumbnail;
            thumbnail.alt = result.title || 'Video thumbnail';
            thumbnail.className = 'result-thumbnail';
            resultElement.appendChild(thumbnail);
        }
        
        // Add title and link
        const titleLink = document.createElement('a');
        titleLink.href = result.url;
        titleLink.textContent = result.title || 'Untitled Video';
        titleLink.target = '_blank';
        titleLink.rel = 'noopener noreferrer';
        titleLink.className = 'result-title';
        resultElement.appendChild(titleLink);
        
        // Add description if available
        if (result.description) {
            const description = document.createElement('p');
            description.className = 'result-description';
            description.textContent = result.description;
            resultElement.appendChild(description);
        }
        
        // Add metadata
        const metadata = document.createElement('div');
        metadata.className = 'result-metadata';
        metadata.innerHTML = `
            ${result.duration ? `<span>Duration: ${result.duration}</span>` : ''}
            ${result.platform ? `<span>Platform: ${result.platform}</span>` : ''}
        `;
        resultElement.appendChild(metadata);
    } else if (result.type === 'website') {
        // Add website icon
        const iconContainer = document.createElement('div');
        iconContainer.className = 'website-icon';
        if (result.favicon) {
            const icon = document.createElement('img');
            icon.src = result.favicon;
            icon.alt = 'Website icon';
            iconContainer.appendChild(icon);
        }
        resultElement.appendChild(iconContainer);
        
        // Add website content
        const contentContainer = document.createElement('div');
        contentContainer.className = 'website-content';
        
        // Add title and link
        const titleLink = document.createElement('a');
        titleLink.href = result.url;
        titleLink.textContent = result.title || result.url;
        titleLink.target = '_blank';
        titleLink.rel = 'noopener noreferrer';
        titleLink.className = 'result-title';
        contentContainer.appendChild(titleLink);
        
        // Add URL
        const urlText = document.createElement('div');
        urlText.className = 'website-url';
        urlText.textContent = result.url;
        contentContainer.appendChild(urlText);
        
        // Add description if available
        if (result.description) {
            const description = document.createElement('p');
            description.className = 'result-description';
            description.textContent = result.description;
            contentContainer.appendChild(description);
        }
        
        resultElement.appendChild(contentContainer);
    }
    
    resultsContainer.appendChild(resultElement);
}

// Event Listeners
if (searchForm) {
    searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const query = searchInput.value.trim();
        
        if (!query) {
            updateStatus('Please enter a search query', 'error');
            return;
        }
        
        if (!socket.connected) {
            updateStatus('Not connected to server. Please wait...', 'error');
            return;
        }
        
        const searchTypes = {
            videos: searchVideos.checked,
            websites: searchWebsites.checked
        };
        
        if (!searchTypes.videos && !searchTypes.websites) {
            updateStatus('Please select at least one search type (Videos or Websites)', 'error');
            return;
        }
        
        socket.emit('search_query', { query, searchTypes });
    });
}

// Initialize
updateStatus('Ready to search', 'info');

// Add CSS styles for the Show More button and video container
const style = document.createElement('style');
style.textContent = `
    .show-more-button {
        display: block;
        width: 100%;
        padding: 10px;
        margin: 20px 0;
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 5px;
        cursor: pointer;
        font-size: 14px;
        color: #495057;
        transition: all 0.2s ease;
    }
    
    .show-more-button:hover {
        background-color: #e9ecef;
        border-color: #ced4da;
    }
    
    .result {
        margin-bottom: 20px;
        padding: 15px;
        border: 1px solid #dee2e6;
        border-radius: 5px;
        background-color: white;
    }
    
    .watch-button {
        margin-left: 10px;
        padding: 5px 10px;
        background-color: #dc3545;
        color: white;
        border: none;
        border-radius: 3px;
        cursor: pointer;
        font-size: 12px;
        transition: all 0.2s ease;
        display: inline-flex;
        align-items: center;
    }
    
    .watch-button:hover {
        background-color: #c82333;
    }
    
    .video-container {
        margin-top: 15px;
        position: relative;
        width: 100%;
        padding-bottom: 56.25%; /* 16:9 aspect ratio */
        height: 0;
        overflow: hidden;
        background-color: #f8f9fa;
        border-radius: 5px;
    }
    
    .video-container iframe {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        border: none;
    }
    
    .fas {
        margin-right: 5px;
    }
    
    .result-header {
        display: flex;
        align-items: center;
        margin-bottom: 10px;
    }
    
    .favicon {
        width: 16px;
        height: 16px;
        margin-right: 10px;
    }
    
    .result-title {
        color: #1a0dab;
        text-decoration: none;
        font-size: 18px;
        font-weight: 500;
    }
    
    .result-title:hover {
        text-decoration: underline;
    }
    
    .result-description {
        color: #4d5156;
        margin: 5px 0;
        line-height: 1.4;
    }
    
    .result-source {
        color: #202124;
        font-size: 13px;
        display: flex;
        align-items: center;
    }
`;
document.head.appendChild(style);

// Add Font Awesome for icons
const fontAwesome = document.createElement('link');
fontAwesome.rel = 'stylesheet';
fontAwesome.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css';
document.head.appendChild(fontAwesome);
