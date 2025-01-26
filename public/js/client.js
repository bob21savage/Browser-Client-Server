// Get the server URL dynamically
const serverUrl = window.location.hostname === 'browser-client-server.vercel.app'
    ? 'https://browser-client-server.vercel.app'
    : `http://${window.location.hostname}:5001`;  // Use the actual hostname instead of hardcoding localhost

console.log('Connecting to server:', serverUrl);

// Connect to Socket.IO server
const socket = io(serverUrl, {
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    timeout: 20000,
    transports: ['polling', 'websocket'],
    upgrade: true,
    withCredentials: false,
    forceNew: true,
    autoConnect: true
});

// Store tags globally
let allTags = new Set();
let selectedTags = new Set();

// DOM Elements
const searchForm = document.getElementById('search-form');
const searchInput = document.getElementById('search-input');
const searchButton = document.getElementById('search-button');
const searchVideos = document.getElementById('search-videos');
const searchWebsites = document.getElementById('search-websites');
const resultsContainer = document.getElementById('results');
const statusElement = document.getElementById('status');
const loaderElement = document.getElementById('loader');
const statsElement = document.getElementById('stats');
const recommendedTagsContainer = document.getElementById('recommended-tags');
const popularTagsContainer = document.getElementById('popular-tags');
const websiteInput = document.getElementById('website-input');
const tagInput = document.getElementById('tag-input');

let searchInProgress = false;
let totalResults = 0;
let videoResults = 0;
let websiteResults = 0;

let allResults = [];
let currentlyDisplayedResults = 0;
const resultsPerPage = 5;

// Tag handling functions
function addTag(tag, container, isSelected = false) {
    const tagElement = document.createElement('div');
    tagElement.className = `tag ${isSelected ? 'selected' : ''}`;
    tagElement.textContent = tag.trim();
    tagElement.onclick = () => toggleTag(tagElement, tag.trim());
    container.appendChild(tagElement);
}

function toggleTag(element, tag) {
    if (selectedTags.has(tag)) {
        selectedTags.delete(tag);
        element.classList.remove('selected');
    } else {
        selectedTags.add(tag);
        element.classList.add('selected');
    }
    // Update search with selected tags
    if (searchInput.value) {
        startSearch();
    }
}

function updateRecommendedTags(searchQuery) {
    // Clear previous recommendations
    recommendedTagsContainer.innerHTML = '';
    
    // Find relevant tags based on search query
    const relevantTags = Array.from(allTags).filter(tag => 
        tag.toLowerCase().includes(searchQuery.toLowerCase()) ||
        searchQuery.toLowerCase().includes(tag.toLowerCase())
    );
    
    // Display recommended tags
    relevantTags.forEach(tag => addTag(tag, recommendedTagsContainer));
}

function submitWebsiteAndTags() {
    const website = websiteInput.value.trim();
    const tags = tagInput.value.trim().split(',').map(tag => tag.trim()).filter(tag => tag);
    
    if (!website) {
        updateStatus('Please enter a website URL', 'error');
        return;
    }
    
    if (tags.length === 0) {
        updateStatus('Please enter at least one tag', 'error');
        return;
    }
    
    // Add new tags to our collection
    tags.forEach(tag => allTags.add(tag));
    
    // Emit website and tags to server
    socket.emit('submit_website_and_tags', { website, tags });
    
    // Clear inputs
    websiteInput.value = '';
    tagInput.value = '';
    
    updateStatus('Website and tags submitted successfully!', 'success');
    updatePopularTags();
}

function updatePopularTags() {
    // Clear current popular tags
    popularTagsContainer.innerHTML = '';
    
    // Get tag frequency
    const tagFrequency = {};
    Array.from(allTags).forEach(tag => {
        tagFrequency[tag] = (tagFrequency[tag] || 0) + 1;
    });
    
    // Sort tags by frequency
    const sortedTags = Object.entries(tagFrequency)
        .sort(([,a], [,b]) => b - a)
        .slice(0, 10) // Show top 10 tags
        .map(([tag]) => tag);
    
    // Display popular tags
    sortedTags.forEach(tag => addTag(tag, popularTagsContainer));
}

function updateSearchStats() {
    if (statsElement) {
        statsElement.innerHTML = `
            <div class="search-stats">
                <span>Total Results: ${totalResults}</span>
                <span>Videos: ${videoResults}</span>
                <span>Websites: ${websiteResults}</span>
            </div>
        `;
    }
}

function addSearchResult(result) {
    if (!result || !resultsContainer) return;

    const resultElement = document.createElement('div');
    resultElement.className = `result-item ${result.type || 'website'}`;

    if (result.type === 'video') {
        // Video result
        const videoContent = `
            <div class="video-thumbnail">
                ${result.thumbnail ? `<img src="${result.thumbnail}" alt="Video thumbnail">` : ''}
            </div>
            <div class="video-info">
                <h3 class="video-title">
                    <a href="${result.url}" target="_blank" rel="noopener noreferrer">
                        ${result.title || 'Untitled Video'}
                    </a>
                </h3>
                <p class="video-description">${result.description || ''}</p>
                <div class="video-metadata">
                    <span class="video-source">${result.source || 'Unknown source'}</span>
                    ${result.duration ? `<span class="video-duration">${result.duration}</span>` : ''}
                </div>
                <button class="watch-button" onclick="handleWatchClick(this.parentElement, '${result.url}')">
                    Watch Video
                </button>
                <div class="video-container" style="display: none;"></div>
            </div>
        `;
        resultElement.innerHTML = videoContent;
        videoResults++;
    } else {
        // Website result
        const websiteContent = `
            <div class="website-icon">
                ${result.favicon ? `<img src="${result.favicon}" alt="Website icon">` : ''}
            </div>
            <div class="website-info">
                <h3 class="website-title">
                    <a href="${result.url}" target="_blank" rel="noopener noreferrer">
                        ${result.title || result.url}
                    </a>
                </h3>
                <p class="website-description">${result.description || ''}</p>
                <div class="website-metadata">
                    <span class="website-url">${result.url}</span>
                </div>
            </div>
        `;
        resultElement.innerHTML = websiteContent;
        websiteResults++;
    }

    // Add tags if present
    if (result.tags && result.tags.length > 0) {
        const tagsContainer = document.createElement('div');
        tagsContainer.className = 'result-tags';
        result.tags.forEach(tag => {
            const tagElement = document.createElement('span');
            tagElement.className = 'tag';
            tagElement.textContent = tag;
            tagElement.onclick = () => toggleTag(tagElement, tag);
            tagsContainer.appendChild(tagElement);
        });
        resultElement.appendChild(tagsContainer);
    }

    resultsContainer.appendChild(resultElement);
    totalResults++;
    updateSearchStats();
}

function startSearch() {
    if (searchInProgress) {
        updateStatus('Search already in progress...', 'info');
        return;
    }

    const query = searchInput.value.trim();
    if (!query) {
        updateStatus('Please enter a search query', 'error');
        return;
    }

    // Check if at least one search type is selected
    if (!searchVideos.checked && !searchWebsites.checked) {
        updateStatus('Please select at least one search type (Videos or Websites)', 'error');
        return;
    }

    clearResults();
    showLoader();
    searchInProgress = true;
    totalResults = 0;
    videoResults = 0;
    websiteResults = 0;
    updateStatus('Starting search...', 'info');

    // Include selected tags and search types in search
    const searchData = {
        query,
        tags: Array.from(selectedTags),
        searchTypes: {
            videos: searchVideos.checked,
            websites: searchWebsites.checked
        }
    };

    socket.emit('search_query', searchData);
    updateRecommendedTags(query);
}

function clearResults() {
    if (resultsContainer) {
        resultsContainer.innerHTML = '';
    }
    if (statsElement) {
        statsElement.innerHTML = '';
    }
    totalResults = 0;
    videoResults = 0;
    websiteResults = 0;
}

function showLoader() {
    if (!loaderElement) return;
    loaderElement.style.display = 'block';
}

function hideLoader() {
    if (!loaderElement) return;
    loaderElement.style.display = 'none';
}

function updateStatus(message, type = 'info') {
    if (statusElement) {
        statusElement.textContent = message;
        statusElement.className = `status status-${type}`;
    }
}

// Socket.IO event handlers
socket.on('connect', () => {
    console.log('Connected to server');
    updateStatus('Connected to server', 'success');
    if (searchButton) searchButton.disabled = false;
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
    updateStatus('Disconnected from server', 'error');
    if (searchButton) searchButton.disabled = true;
});

socket.on('connect_error', (error) => {
    console.error('Connection error:', error);
    updateStatus('Connection error: ' + error.message, 'error');
});

socket.on('connect_timeout', () => {
    console.error('Connection timeout');
    updateStatus('Connection timeout', 'error');
});

socket.on('reconnect_attempt', (attemptNumber) => {
    console.log('Attempting to reconnect:', attemptNumber);
    updateStatus('Attempting to reconnect... (Attempt ' + attemptNumber + ')', 'info');
});

socket.on('search_started', (data) => {
    console.log('Search started:', data);
    updateStatus(data.message, 'info');
    clearResults();
    showLoader();
    if (searchButton) searchButton.disabled = true;
    totalResults = 0;
    videoResults = 0;
    websiteResults = 0;
});

socket.on('new_result', (data) => {
    console.log('New result:', data);
    if (data.result) {
        addSearchResult(data.result);
    }
});

socket.on('search_completed', (data) => {
    console.log('Search completed:', data);
    hideLoader();
    updateStatus(`Search completed. Found ${data.total} results.`, 'success');
    if (searchButton) searchButton.disabled = false;
    searchInProgress = false;
});

socket.on('search_error', (data) => {
    console.error('Search error:', data);
    hideLoader();
    updateStatus(`Error: ${data.error}`, 'error');
    if (searchButton) searchButton.disabled = false;
    searchInProgress = false;
});

// Helper Functions
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

// Event Listeners
if (searchForm) {
    searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        startSearch();
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
