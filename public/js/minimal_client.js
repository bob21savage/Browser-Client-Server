// Minimal client-side JavaScript for testing

// Define the server URL
const serverUrl = 'http://127.0.0.1:5001'; // Use localhost for development

// Connect to Socket.IO server (commented out for testing)
// const socket = io(serverUrl);

// DOM Elements
const searchForm = document.getElementById('search-form');
const searchInput = document.getElementById('search-input');

// Basic functionality to log input
if (searchForm) {
    searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const query = searchInput.value;
        console.log('Search query:', query);
        // Further functionality can be added here
    });
}
