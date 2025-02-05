// Get the server URL dynamically
const serverUrl = 'https://browser-client-server.onrender.com/'; // Update the Socket.IO connection URL for production

// Connect to Socket.IO server
const socket = io(serverUrl, {
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    timeout: 20000,
    transports: ['polling', 'websocket'],  // Try polling first, then upgrade to websocket
    upgrade: true,
    withCredentials: true,
    forceNew: true
});

// DOM Elements
const searchForm = document.getElementById('search-form');
const searchInput = document.getElementById('search-input');
const searchButton = document.getElementById('search-button');
const resultsContainer = document.getElementById('results');
const statusElement = document.getElementById('status');
const statsElement = document.getElementById('stats');
const pageInfoElement = document.getElementById('page-info');
const prevPageButton = document.getElementById('prev-page');
const nextPageButton = document.getElementById('next-page');
const downloadButton = document.getElementById('download-selected');

let totalResults = 0;
let currentPage = 1;
const resultsPerPage = 10;
let query = '';

// Socket.IO event handlers
socket.on('connect', () => {
    console.log('Connected to Flask server');
    updateStatus('Connected to server', 'success');
    if (searchButton) searchButton.disabled = false;
});

socket.on('disconnect', () => {
    console.log('Disconnected from Flask server');
    updateStatus('Disconnected from server', 'error');
    if (searchButton) searchButton.disabled = true;
});

socket.on('search_started', (data) => {
    console.log('Search started:', data);
    updateStatus(data.message, 'info');
    clearResults();
    showLoadingIndicator();
    if (searchButton) searchButton.disabled = true;
    totalResults = 0;
});

socket.on('new_result', (data) => {
    console.log('New result:', data);
    if (data.result) {
        totalResults++;
        addSearchResult(data.result);
        updateSearchStats({ total: totalResults });
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
            <span class="stat-item">Results Found: ${data.total || 0}</span>
            ${data.query ? `<span class="stat-item">Query: ${data.query}</span>` : ''}
        </div>
    `;
}

function createVideoEmbed(url) {
    if (!url) return '';
    
    let embedHtml = '';
    try {
        if (url.includes('youtube.com') || url.includes('youtu.be')) {
            const videoId = url.includes('youtube.com') ? 
                url.split('v=')[1]?.split('&')[0] :
                url.split('youtu.be/')[1]?.split('?')[0];
                
            if (videoId) {
                embedHtml = `<iframe 
                    width="560" 
                    height="315" 
                    src="https://www.youtube.com/embed/${videoId}" 
                    frameborder="0" 
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                    allowfullscreen>
                </iframe>`;
            }
        } else if (url.includes('vimeo.com')) {
            const videoId = url.split('vimeo.com/')[1]?.split('?')[0];
            if (videoId) {
                embedHtml = `<iframe 
                    width="560" 
                    height="315" 
                    src="https://player.vimeo.com/video/${videoId}" 
                    frameborder="0" 
                    allow="autoplay; fullscreen; picture-in-picture" 
                    allowfullscreen>
                </iframe>`;
            }
        } else if (url.includes('dailymotion.com')) {
            const videoId = url.split('dailymotion.com/video/')[1]?.split('?')[0];
            if (videoId) {
                embedHtml = `<iframe 
                    width="560" 
                    height="315" 
                    src="https://www.dailymotion.com/embed/video/${videoId}" 
                    frameborder="0" 
                    allow="autoplay; fullscreen; picture-in-picture" 
                    allowfullscreen>
                </iframe>`;
            }
        }
    } catch (error) {
        console.error('Error creating video embed:', error);
    }
    
    return embedHtml;
}

function addSearchResult(result) {
    if (!resultsContainer || !result) return;
    
    const resultElement = document.createElement('div');
    resultElement.className = 'result-item';
    
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
        <div class="metadata-item">Source: ${result.source || 'Unknown'}</div>
        ${result.duration ? `<div class="metadata-item">Duration: ${result.duration}</div>` : ''}
        ${result.views ? `<div class="metadata-item">Views: ${result.views}</div>` : ''}
    `;
    resultElement.appendChild(metadata);
    
    // Add checkbox for download
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.className = 'video-checkbox';
    checkbox.dataset.url = result.url;
    resultElement.appendChild(checkbox);
    
    // Add to results container with animation
    resultElement.style.opacity = '0';
    resultsContainer.appendChild(resultElement);
    setTimeout(() => {
        resultElement.style.opacity = '1';
    }, 10);
}

function displayResults(results) {
    const resultsContainer = document.getElementById('results');
    resultsContainer.innerHTML = ''; // Clear previous results

    results.forEach(result => {
        const resultElement = document.createElement('div');
        resultElement.innerHTML = `
            <h3>${result.title}</h3>
            <img src="${result.thumbnail}" alt="${result.title}">
            <p>${result.description}</p>
            <input type="checkbox" class="video-checkbox" data-url="${result.url}"> Select to download
            ${createVideoEmbed(result.url)}
        `;
        resultsContainer.appendChild(resultElement);
    });
}

async function fetchResults() {
    console.log(`Fetching results for query: ${query}, page: ${currentPage}, limit: ${resultsPerPage}`);
    try {
        const response = await fetch(`/search_videos?query=${query}&page=${currentPage}&limit=${resultsPerPage}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        console.log("Query parameters:", { query, page: currentPage, limit: resultsPerPage });
        console.log("Response data:", data);
        
        if (data && Array.isArray(data.results)) {
            displayResults(data.results);
            updatePagination(data.count);
        } else {
            console.error("Unexpected response structure:", data);
        }
    } catch (error) {
        console.error("Fetch error:", error);
    }
}

function updatePagination(totalResults) {
    const totalPages = Math.ceil(totalResults / resultsPerPage);
    pageInfoElement.innerText = `Page ${currentPage} of ${totalPages}`;
    prevPageButton.disabled = currentPage === 1;
    nextPageButton.disabled = currentPage === totalPages;
}

prevPageButton.addEventListener('click', () => {
    if (currentPage > 1) {
        currentPage--;
        fetchResults();
    }
});

nextPageButton.addEventListener('click', () => {
    currentPage++;
    fetchResults();
});

// Event Listeners
if (searchForm) {
    searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        query = searchInput.value.trim();
        
        if (!query) {
            updateStatus('Please enter a search query', 'error');
            return;
        }
        
        if (!socket.connected) {
            updateStatus('Not connected to server. Please wait...', 'error');
            return;
        }
        
        currentPage = 1;
        fetchResults();
    });
}

if (downloadButton) {
    downloadButton.addEventListener('click', async () => {
        const selectedVideos = Array.from(document.querySelectorAll('.video-checkbox:checked')).map(cb => cb.dataset.url);
        
        if (selectedVideos.length > 0) {
            const response = await fetch('/download_videos', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ urls: selectedVideos })
            });
            
            if (response.ok) {
                console.log('Download started for selected videos.');
            } else {
                console.error('Failed to start download.');
            }
        } else {
            alert('Please select at least one video to download.');
        }
    });
}

// Initialize
updateStatus('Ready to search', 'info');
