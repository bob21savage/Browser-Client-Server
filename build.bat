@echo on
setlocal enabledelayedexpansion

echo Cleaning previous builds...
if exist "dist" rd /s /q "dist"
if exist "build" rd /s /q "build"
mkdir dist
mkdir dist\video-scraper

echo Installing Python dependencies...
call python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install Python dependencies
    exit /b 1
)

echo Installing Node dependencies...
call npm install
if errorlevel 1 (
    echo Failed to install Node dependencies
    exit /b 1
)

echo Building Python application...
call python -m PyInstaller app.spec --distpath dist\video-scraper
if errorlevel 1 (
    echo Failed to build Python application
    exit /b 1
)

echo Building Node.js application...
call npx pkg . --targets node18-win-x64 --output dist\video-scraper\video-scraper-node.exe
if errorlevel 1 (
    echo Failed to build Node.js application
    exit /b 1
)

echo Copying required files...
if exist "public" (
    xcopy /E /I /Y "public" "dist\video-scraper\public\"
) else (
    echo Warning: public directory not found
)

if exist "templates" (
    xcopy /E /I /Y "templates" "dist\video-scraper\templates\"
) else (
    echo Warning: templates directory not found
)

echo Creating start script...
(
echo @echo on
echo echo Starting Video Scraper...
echo cd /d "%%~dp0"
echo.
echo echo Starting Python backend server...
echo start /wait "" "video-scraper.exe"
echo if errorlevel 1 ^(
echo     echo Failed to start Python server
echo     pause
echo     exit /b 1
echo ^)
echo.
echo echo Starting Node.js frontend server...
echo start /wait "" "video-scraper-node.exe"
echo if errorlevel 1 ^(
echo     echo Failed to start Node.js server
echo     pause
echo     exit /b 1
echo ^)
echo.
echo echo Both servers started successfully!
echo echo Open your web browser and navigate to: http://localhost:5001
echo pause
) > "dist\video-scraper\start.bat"

echo Moving Python executable...
move "dist\video-scraper.exe" "dist\video-scraper\"

echo Build complete! Your packaged application is in the dist/video-scraper directory.
echo To start the application, run start.bat in the dist/video-scraper directory.

dir /s /b dist\video-scraper
