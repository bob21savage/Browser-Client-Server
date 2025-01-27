// This file will be renamed to server.cjs
const { app, BrowserWindow } = require('electron');
const { exec } = require('child_process');

// This will be called when Electron is ready
app.whenReady().then(() => {
    app.setPath('userData', __dirname); // Set the cache path to the app folder
    createWindow();
});

// Function to create a new browser window
function createWindow() {
    const mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
        },
    });

    mainWindow.loadURL(`http://localhost:3000`); // Load your serverless function
}

// Path to the Python script
const pythonScriptPath = './app.py'; // Update to point to app.py in the main root directory

// Function to run the Python script
function runPythonScript() {
    exec(`python ${pythonScriptPath}`, (error, stdout, stderr) => {
        if (error) {
            console.error(`Error executing script: ${error}`);
            return;
        }
        console.log(`Python script output: ${stdout}`);
        if (stderr) {
            console.error(`stderr: ${stderr}`);
        }
    });
}

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