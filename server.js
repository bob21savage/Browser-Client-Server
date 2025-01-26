const { app, BrowserWindow } = require('electron');
const express = require('express');
const cors = require('cors'); // Import the cors module
const { exec } = require('child_process');
const http = require('http');
const { Server } = require('socket.io');

const expressApp = express();
const PORT = 5001; // Updated Express server port

// Path to the Python script
const pythonScriptPath = 'C:\\Users\\bpier\\Desktop\\scrape\\scrape\\my app\\scrape\\scrape_upgrade.py';

// Function to run the Python script
function runPythonScript() {
    exec(`python ${pythonScriptPath}`, (error, stdout, stderr) => {
        if (error) {
            console.error(`Error executing script: ${error}`);
            return;
        }
        console.log(`Output: ${stdout}`);
        if (stderr) {
            console.error(`stderr: ${stderr}`);
        }
    });
}

// Function to create a new browser window
function createWindow() {
    const win = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
        }
    });

    win.loadURL(`http://localhost:${PORT}`); // Load your Express app
}

// This will be called when Electron is ready
app.whenReady().then(() => {
    createWindow();

    // Create an HTTP server using the Express app
    const httpServer = http.createServer(expressApp);

    // Initialize Socket.IO with the HTTP server
    const io = new Server(httpServer);

    // Handle WebSocket connections
    io.on('connection', (socket) => {
        console.log('A user connected');

        // Handle disconnection
        socket.on('disconnect', () => {
            console.log('User disconnected');
        });
    });

    // Start Express server
    expressApp.use(express.static('templates'));
    expressApp.get('/', (req, res) => {
        res.sendFile(__dirname + '/templates/index.html');
    });

    expressApp.use(cors({
        origin: 'https://browser-client-server.vercel.app', // Allow only your Vercel URL
        methods: ['GET', 'POST', 'OPTIONS'],
        credentials: true
    }));

    expressApp.use((req, res, next) => {
        res.setHeader('Cache-Control', 'no-store');
        res.setHeader('X-Content-Type-Options', 'nosniff');
        next();
    });

    // Update the Express server to listen on the same port as the HTTP server
    httpServer.listen(PORT, () => {
        console.log(`Express server with WebSocket is running on http://localhost:${PORT}`);
    });

    app.on('window-all-closed', () => {
        if (process.platform !== 'darwin') {
            app.quit();
        }
    });

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });

    // Call the function to run the Python script
    runPythonScript();
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});