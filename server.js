const { app, BrowserWindow } = require('electron');
const express = require('express');
const { exec } = require('child_process');
const axios = require('axios');

const expressApp = express();
const PORT = 5001; // Express server port

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

    win.loadURL(`http://0.0.0.0:${PORT}`); // Load your Express app
}

// Function to fetch data from the external server
async function fetchData() {
    try {
        const response = await axios.get('https://browser-client-server-g620gwi30-bob21savages-projects.vercel.app/');
        console.log('Data received:', response.data);
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

// This will be called when Electron is ready
app.whenReady().then(() => {
    createWindow();

    // Start Express server
    expressApp.use(express.static('templates'));
    expressApp.get('/', (req, res) => {
        res.sendFile(__dirname + '/templates/index.html');
    });
    expressApp.listen(PORT, '0.0.0.0', () => {
        console.log(`Server is running on http://0.0.0.0:${PORT}`);
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

    // Call the fetchData function
    fetchData();
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});