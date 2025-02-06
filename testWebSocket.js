import WebSocket from 'ws';

const socket = new WebSocket('wss://browser-client-server.onrender.com/socket.io/?EIO=4&transport=websocket');

socket.on('open', function() {
    console.log('WebSocket connection established.');
});

socket.on('message', function(data) {
    const message = data.toString(); // Convert Buffer to string
    console.log('Message from server:', message);
});

socket.on('error', function(error) {
    console.error('WebSocket error:', error);
});

socket.on('close', function(code, reason) {
    console.log('WebSocket connection closed:', code, reason);
});
