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
        console.log('Search query:', query);

        await search(query);
    });
}

async function search(query) {
    const response = await fetch('/api/search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
    });

    if (!response.ok) {
        const errorData = await response.json();
        console.error('API Error:', errorData);
        alert('Error: ' + errorData.message);
        return;
    }

    const data = await response.json();
    console.log('Response:', data);
    if (data.result === 'success') {
        displayResults(data.results); // Call a function to display results
    } else {
        console.error('Search failed:', data);
    }
}

function displayResults(results) {
    resultsContainer.innerHTML = ''; // Clear previous results
    results.forEach(result => {
        const resultElement = document.createElement('div');
        resultElement.innerHTML = `<h3>${result.title}</h3><a href="${result.url}">${result.url}</a>`;
        resultsContainer.appendChild(resultElement);
    });
}
