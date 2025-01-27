// Minimal client-side JavaScript for testing

// Define the server URL
const serverUrl = 'http://127.0.0.1:5001'; // Use localhost for development

// DOM Elements
const searchForm = document.getElementById('search-form');
const searchInput = document.getElementById('search-input');
const resultsContainer = document.getElementById('results'); // Assuming you have a div with this ID

// Basic functionality to log input and make a fetch request
if (searchForm) {
    searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const query = searchInput.value;
        console.log('Search query:', query);

        // Fetch request to send the search query to the server
        fetch(`${serverUrl}/api/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query }),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Response:', data);
            if (data.result === 'success') {
                displayResults(data.results); // Call a function to display results
            } else {
                console.error('Search failed:', data);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });
}

function displayResults(results) {
    resultsContainer.innerHTML = ''; // Clear previous results
    results.forEach(result => {
        const resultElement = document.createElement('div');
        resultElement.innerHTML = `<h3>${result.title}</h3><a href="${result.url}">${result.url}</a>`;
        resultsContainer.appendChild(resultElement);
    });
}
