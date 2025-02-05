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
    if (data.error) {
        console.error(data.error);
        alert(data.error); // Show an alert to the user
        return;
    }
    updateStatus(`Search completed. Found ${data.total} results.`, 'success');
    updateSearchStats(data);
    if (searchButton) searchButton.disabled = false;
});

socket.on('search_error', (data) => {
    console.error('Search error:', data);
    hideLoadingIndicator();
    if (data.error) {
        console.error(data.error);
        alert(data.error); // Show an alert to the user
        return;
    }
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

// Event Listeners
if (searchForm) {
    searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        }
    });
}

if (searchHistoryButton) {
    searchHistoryButton.addEventListener('click', async () => {
        try {
            const response = await fetch('/search_history', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${process.env.API_KEY}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error('Network response was not ok: ' + response.statusText);
            }

            const data = await response.json();
            displaySearchHistory(data);
        } catch (error) {
            console.error('Error fetching search history:', error);
        }
    });
}

// Initialize
updateStatus('Ready to search', 'info');
