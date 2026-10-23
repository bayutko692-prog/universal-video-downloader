#!/usr/bin/env python3
"""
Universal Video Downloader Web UI - Built by promode for boss @dvc
"""

import os
import subprocess
import threading
from flask import Flask, render_template, request, jsonify, send_from_directory

app = Flask(__name__)
DOWNLOAD_FOLDER = os.path.abspath("downloads")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

download_status = {"status": "idle", "message": "Ready to download", "filename": None}

def run_download(url):
    global download_status
    download_status["status"] = "downloading"
    download_status["message"] = f"Downloading video from {url}..."
    download_status["filename"] = None

    output_template = os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s')
    
    # 1. Try yt-dlp
    cmd = [
        "yt-dlp",
        "-o", output_template,
        "--no-playlist",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        url
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        # Find latest file in downloads
        files = os.listdir(DOWNLOAD_FOLDER)
        if files:
            latest_file = max([os.path.join(DOWNLOAD_FOLDER, f) for f in files], key=os.path.getctime)
            fname = os.path.basename(latest_file)
            download_status["status"] = "completed"
            download_status["message"] = f"Successfully downloaded: {fname}"
            download_status["filename"] = fname
            return

    # 2. Fallback smart scraping if yt-dlp direct fails
    import requests
    from bs4 import BeautifulSoup
    import re
    from urllib.parse import urljoin

    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        soup = BeautifulSoup(resp.text, 'html.parser')
        candidates = []
        for iframe in soup.find_all('iframe', src=True):
            candidates.append(urljoin(url, iframe['src']))
        for video in soup.find_all('video'):
            if video.get('src'): candidates.append(urljoin(url, video['src']))
            for s in video.find_all('source'):
                if s.get('src'): candidates.append(urljoin(url, s['src']))
        
        url_pattern = re.compile(r'https?://[^\s<>"]+?\.(?:mp4|m3u8|webm|mkv|mov)(?:\?[^\s<>"]*)?', re.IGNORECASE)
        for fu in url_pattern.findall(resp.text):
            candidates.append(fu)

        success = False
        for i, target in enumerate(set(candidates), 1):
            sub_cmd = ["yt-dlp", "-o", os.path.join(DOWNLOAD_FOLDER, f"scraped_{i}.%(ext)s"), target]
            res = subprocess.run(sub_cmd)
            if res.returncode == 0:
                files = os.listdir(DOWNLOAD_FOLDER)
                latest_file = max([os.path.join(DOWNLOAD_FOLDER, f) for f in files], key=os.path.getctime)
                fname = os.path.basename(latest_file)
                download_status["status"] = "completed"
                download_status["message"] = f"Successfully downloaded via fallback: {fname}"
                download_status["filename"] = fname
                success = True
                break

        if not success:
            download_status["status"] = "error"
            download_status["message"] = "Failed to download video from all extracted sources."
    except Exception as e:
        download_status["status"] = "error"
        download_status["message"] = f"Error: {str(e)}"

@app.route('/')
def index():
    files = os.listdir(DOWNLOAD_FOLDER)
    file_list = [f for f in files if os.path.isfile(os.path.join(DOWNLOAD_FOLDER, f))]
    return render_template('index.html', files=file_list)

@app.route('/api/download', methods=['POST'])
def api_download():
    data = request.get_json() or {}
    url = data.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    if download_status["status"] == "downloading":
        return jsonify({"error": "A download is already in progress"}), 400

    thread = threading.Thread(target=run_download, args=(url,))
    thread.daemon = True
    thread.start()
    return jsonify({"success": True, "message": "Download started in background"})

@app.route('/api/status')
def api_status():
    return jsonify(download_status)

@app.route('/downloads/<path:filename>')
def download_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

@app.route('/api/files')
def api_files():
    files = os.listdir(DOWNLOAD_FOLDER)
    file_list = [f for f in files if os.path.isfile(os.path.join(DOWNLOAD_FOLDER, f))]
    return jsonify(file_list)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
