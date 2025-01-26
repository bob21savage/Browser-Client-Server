@echo off
echo Stopping running processes...
taskkill /F /IM video-scraper.exe 2>nul
taskkill /F /IM video-scraper-node.exe 2>nul
echo Done!
