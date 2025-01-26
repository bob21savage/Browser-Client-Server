import React, { useEffect, useState } from 'react';

const VideoDisplay = () => {
    const [urls, setUrls] = useState([]);

    useEffect(() => {
        const fetchUrls = async () => {
            try {
                const response = await fetch('/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({}) // Send any necessary payload here
                });
                const data = await response.json();
                setUrls(data.links); // Assuming the response contains a 'links' array

                // Check if there are any URLs and set the iframe src
                if (data.links.length > 0) {
                    document.getElementById('videoIframe').src = data.links[0]; // Set to the first URL
                } else {
                    console.error('No URLs found to display in the iframe.');
                }
            } catch (error) {
                console.error('Error fetching URLs:', error);
            }
        };

        fetchUrls();
    }, []);

    return (
        <div>
            <iframe id="videoIframe" src="" width="600" height="400" style={{ border: '1px solid black' }}></iframe>
        </div>
    );
};

export default VideoDisplay;
