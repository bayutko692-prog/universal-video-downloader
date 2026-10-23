#!/bin/bash
cd /root/video-downloader-web
while true; do
    echo "[*] Starting Universal Video Downloader Web App..." >> run.log 2>&1
    python3 app.py >> app.log 2>&1
    echo "[!] App stopped. Restarting..." >> run.log 2>&1
    sleep 3
done
