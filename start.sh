#!/bin/bash
pip install flask requests beautifulsoup4 rich yt-dlp
sudo apt-get update && sudo apt-get install -y ffmpeg
nohup python3 app.py > app.log 2>&1 &
echo "[+] Universal Video Downloader is running on port 5000!"
