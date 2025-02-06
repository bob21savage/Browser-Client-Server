import express from 'express';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import cors from 'cors';
import { createProxyMiddleware } from 'http-proxy-middleware';
import { io } from 'socket.io-client';
import open from 'open';
import http from 'http';
import WebSocket from 'ws';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
const server = http.createServer(app);
const port = process.env.PORT || 3000;
const flaskUrl = process.env.FLASK_URL || 'http://localhost:5001';

// Enable CORS
app.use(cors({
    origin: "*",
    methods: ['GET', 'POST', 'OPTIONS'],
    credentials: true
}));

// Serve static files
app.use(express.static(join(__dirname, 'public')));
app.use(express.static(join(__dirname, 'src')));

// Socket.IO connection to Flask server
const socket = io('https://browser-client-server.onrender.com', {
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
});

let retryCount = 0;
const maxRetries = 5;

function connectWithRetry() {
    if (retryCount >= maxRetries) {
        console.error('Max retry attempts reached. Please check if Flask server is running.');
        return;
    }
    console.log(`Attempting to connect to Flask server (attempt ${retryCount + 1}/${maxRetries})...`);
    socket.connect();
}

// Socket.IO event handlers
socket.on('connect', () => {
    console.log('Connected to Flask WebSocket server');
    retryCount = 0;
});

socket.on('connect_error', (error) => {
    console.error('Connection error:', error);
    retryCount++;
    setTimeout(connectWithRetry, 2000);
});

socket.on('disconnect', () => {
    console.log('Disconnected from Flask server');
});

// WebSocket client
const ws = new WebSocket('wss://browser-client-server.onrender.com/socket.io/?EIO=4&transport=websocket');

ws.on('open', function() {
    console.log('WebSocket connection established.');
});

ws.on('message', function(data) {
    const message = data.toString();
    console.log('Message from server:', message);
});

ws.on('error', function(error) {
    console.error('WebSocket error:', error);
});

ws.on('close', function(code, reason) {
    console.log('WebSocket connection closed:', code, reason);
});

// Proxy configuration
const proxyOptions = {
    target: flaskUrl,
    changeOrigin: true,
    ws: true,  // Enable WebSocket proxy
    secure: false,
    logLevel: 'debug',
    onError: (err, req, res) => {
        console.error('Proxy error:', err);
        res.writeHead(500, {
            'Content-Type': 'text/plain'
        });
        res.end('Proxy error: ' + err);
    },
    onProxyReq: (proxyReq, req, res) => {
        // Add custom headers if needed
        proxyReq.setHeader('X-Special-Proxy-Header', 'video-search');
    }
};

// Apply proxy middleware for API and WebSocket
app.use('/socket.io', createProxyMiddleware({ 
    ...proxyOptions,
    ws: true 
}));

app.use('/api', createProxyMiddleware(proxyOptions));

app.use('/api', createProxyMiddleware({
    target: 'https://browser-client-server.onrender.com',
    changeOrigin: true,
    ws: true,
    pathRewrite: {'^/api' : ''},
    onProxyRes: (proxyRes, req, res) => {
        proxyRes.headers['Access-Control-Allow-Origin'] = '*';
    },
    onProxyReq: (proxyReq, req, res) => {
        proxyReq.setHeader('Upgrade', 'websocket');
        proxyReq.setHeader('Connection', 'upgrade');
    }
}));

// Serve index.html for all other routes
app.get('*', (req, res) => {
    res.sendFile(join(__dirname, 'public', 'index.html'));
});

// Check if port is in use
async function checkPort(port) {
    return new Promise((resolve, reject) => {
        const test_server = http.createServer()
            .listen(port, () => {
                test_server.close();
                resolve(true);
            })
            .on('error', (err) => {
                if (err.code === 'EADDRINUSE') {
                    resolve(false);
                } else {
                    reject(err);
                }
            });
    });
}

// Start server with port checking
async function startServer() {
    let currentPort = port;
    let isPortAvailable = await checkPort(currentPort);
    
    while (!isPortAvailable && currentPort < port + 10) {
        console.log(`Port ${currentPort} is in use, trying ${currentPort + 1}...`);
        currentPort++;
        isPortAvailable = await checkPort(currentPort);
    }
    
    if (!isPortAvailable) {
        console.error('Could not find an available port. Please free up some ports and try again.');
        process.exit(1);
    }
    
    server.listen(currentPort, () => {
        console.log(`Server running at http://localhost:${currentPort}`);
        // Open browser window
        open(`http://localhost:${currentPort}`).catch(() => {
            console.log('Failed to open browser automatically.');
        });
    });
    
    // Start connection to Flask server
    connectWithRetry();
}

// Handle graceful shutdown
function cleanup() {
    console.log('Shutting down gracefully...');
    socket.close();
    ws.close();
    server.close(() => {
        console.log('Server closed');
        process.exit(0);
    });
}

process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);

// Start the server
startServer().catch(err => {
    console.error('Failed to start server:', err);
    process.exit(1);
});