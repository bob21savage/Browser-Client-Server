const { app, BrowserWindow } = require('electron');
const express = require('express');
const { exec } = require('child_process');

const expressApp = express();
const PORT = 3001; // Express server port

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

    // Start Express server
    expressApp.use(express.static('templates'));
    expressApp.get('/', (req, res) => {
        res.sendFile(__dirname + '/templates/index.html');
    });
    expressApp.listen(PORT, () => {
        console.log(`Express server is running on http://localhost:${PORT}`);
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