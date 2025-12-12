from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from downloader import SocialDownloader
import os

app = Flask(__name__)
CORS(app)

downloader = SocialDownloader(download_path="downloads")

@app.route('/')
def home():
    return '''
    <h1>🎬 Social Media Downloader API</h1>
    <p>Server is running!</p>
    '''

@app.route('/api/info', methods=['POST'])
def get_info():
    """Get media information"""
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'success': False, 'error': 'URL is required'}), 400
    
    result = downloader.get_video_info(url)
    return jsonify(result)

@app.route('/api/download', methods=['POST'])
def download_media():
    """Download media"""
    data = request.json
    url = data.get('url')
    quality = data.get('quality', 'highest')
    format_type = data.get('format', 'mp4')
    download_type = data.get('download_type', 'video')
    
    if not url:
        return jsonify({'success': False, 'error': 'URL is required'}), 400
    
    result = downloader.download(url, quality, format_type, download_type)
    return jsonify(result)

@app.route('/api/file/<filename>', methods=['GET'])
def get_file(filename):
    """Serve downloaded file"""
    try:
        return send_from_directory('downloads', filename, as_attachment=True)
    except:
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🎬 Social Media Downloader Server v2.0")
    print("="*50)
    print("✅ Server starting...")
    print("🌐 Backend: http://localhost:5000")
    print("📁 Open frontend/index.html in browser")
    print("="*50 + "\n")
    
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    
    app.run(debug=True, port=5000, host='0.0.0.0')