// Minimal client-side JavaScript for testing

// Define the server URL
const serverUrl = 'http://127.0.0.1:5001'; // Use localhost for development

// DOM Elements
const searchForm = document.getElementById('search-form');
const searchInput = document.getElementById('search-input');
const resultsContainer = document.getElementById('results'); // Assuming you have a div with this ID

// Basic functionality to log input and make a fetch request
if (searchForm) {
    const button = document.createElement('button');
    button.type = 'submit'; // Set button type
    button.textContent = 'Search'; // Set discernible text
    searchForm.appendChild(button);

    searchForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const query = searchInput.value;
        await search(query);
    });
}

async function search(query) {
    console.log('Search query:', query);
    fetch('http://127.0.0.1:5001/search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query: query })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        console.log('Response:', data);
        // Handle the response data
    })
    .catch(error => {
        console.error('API Error:', error);
        alert('Error: ' + error.message);
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
