import React, { useState } from 'react';
import './App.css';
import VideoDisplay from './VideoDisplay';
import SearchBar from './SearchBar';

function App() {
  const [videoLinks, setVideoLinks] = useState([]);

  const handleSearch = async (query) => {
    const response = await fetch('http://127.0.0.1:5000/search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });

    if (response.ok) {
      const data = await response.json();
      setVideoLinks(data.links); // Assuming the response contains a 'links' array
    } else {
      console.error('Failed to fetch videos');
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Welcome to My React App</h1>
        <p>This is a simple React application.</p>
        <SearchBar onSearch={handleSearch} />
        <VideoDisplay videoLinks={videoLinks} />
      </header>
    </div>
  );
}

export default App;