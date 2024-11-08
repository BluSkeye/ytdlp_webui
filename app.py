from flask import Flask, request, send_file, abort, render_template
import yt_dlp
import uuid
import os
import re
import glob

app = Flask(__name__)

# UUID key for access (you can change this to any UUID string)
ACCESS_KEY = os.environ.get("ACCESS_KEY", str(uuid.uuid4()))

def extract_youtube_id(url):
    pattern = r'(?:https?://)?(?:www\.)?(?:youtube\.com/(?:watch\?v=|embed/|v/|.+\?v=)|youtu\.be/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def download_video(youtube_id):
    ydl_opts = {
        'format': 'best',
        'outtmpl': f'{youtube_id}.%(ext)s'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_id])

def get_downloaded_file(youtube_id):
    # Find the downloaded file with any extension (e.g., mp4, mkv, etc.)
    files = glob.glob(f'{youtube_id}.*')
    return files[0] if files else None

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/download', methods=['POST', 'GET'])
def download():
    if request.method == 'POST':
        data = request.json
        url = data.get('url')
        key = data.get('key')

        print(ACCESS_KEY)

        if key != ACCESS_KEY:
            return abort(403, "Forbidden: Invalid access key.")

        if not re.match(r'^https?://(www\.)?(youtube\.com|youtu\.be)/.+$', url):
            return abort(400, "Invalid YouTube URL format.")

        youtube_id = extract_youtube_id(url)

        try:
            download_video(youtube_id)
            file_path = get_downloaded_file(youtube_id)
            if file_path:
                return {"url": f"/download?id={youtube_id}"}, 200
            else:
                return {"error": "Download failed or file not found"}, 500
        except Exception as e:
            return {"error": str(e)}, 500
    else:
        id = request.args.get('id')
        file_path = get_downloaded_file(id)
        if not file_path:
            return abort(404, "File not found.")
        try:
            return send_file(file_path, as_attachment=True, download_name=os.path.split(file_path)[1])
        finally:
            # Remove the downloaded file after sending it to the client
            if os.path.exists(file_path):
                os.remove(file_path)
