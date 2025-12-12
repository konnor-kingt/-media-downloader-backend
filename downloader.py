import yt_dlp
import os
import re

class SocialDownloader:
    def __init__(self, download_path="downloads"):
        self.download_path = download_path
        if not os.path.exists(download_path):
            os.makedirs(download_path)
    
    def get_video_info(self, url):
        """Get media information without downloading"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Detect content type
                content_type = self._detect_content_type(info)
                
                # Get available qualities
                available_qualities = self._get_available_qualities(info)
                
                # Get available formats
                available_formats = self._get_available_formats(info, content_type)
                
                return {
                    'success': True,
                    'title': info.get('title', 'Unknown'),
                    'thumbnail': info.get('thumbnail'),
                    'duration': info.get('duration'),
                    'platform': info.get('extractor_key', 'Unknown'),
                    'uploader': info.get('uploader', 'Unknown'),
                    'view_count': info.get('view_count'),
                    'content_type': content_type,
                    'available_qualities': available_qualities,
                    'available_formats': available_formats,
                    'description': info.get('description', '')[:200],
                    'width': info.get('width'),
                    'height': info.get('height'),
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _detect_content_type(self, info):
        """Detect if content is video, audio, or photo"""
        
        # Check for photo/image
        if info.get('_type') == 'image':
            return 'photo'
        
        # Check URL patterns for photos
        url = info.get('webpage_url', '') or info.get('url', '')
        if any(x in url.lower() for x in ['/photo/', '/image/', '.jpg', '.png', '.jpeg', '.webp']):
            return 'photo'
        
        # Check if duration is 0 or None (could be photo)
        duration = info.get('duration')
        formats = info.get('formats', [])
        
        # Check if only image formats available
        has_video = any(f.get('vcodec') != 'none' and f.get('vcodec') is not None for f in formats)
        has_audio = any(f.get('acodec') != 'none' and f.get('acodec') is not None for f in formats)
        
        if not has_video and not has_audio:
            return 'photo'
        
        if not has_video and has_audio:
            return 'audio'
        
        # Check for very short duration with no audio (could be GIF/photo)
        if duration is None or duration == 0:
            if not has_audio:
                return 'photo'
        
        return 'video'
    
    def _get_available_qualities(self, info):
        """Find what qualities are actually available"""
        qualities = {}
        
        for f in info.get('formats', []):
            height = f.get('height')
            if height and f.get('vcodec') != 'none':
                quality_label = self._height_to_quality(height)
                if quality_label:
                    # Store the best format for each quality
                    if quality_label not in qualities:
                        qualities[quality_label] = {
                            'height': height,
                            'filesize': f.get('filesize') or f.get('filesize_approx'),
                            'ext': f.get('ext'),
                            'available': True
                        }
        
        # Sort from highest to lowest
        order = ['8k', '4k', '2k', '1080p', '720p', '480p', '360p', '240p', '144p']
        result = []
        for q in order:
            if q in qualities:
                result.append({
                    'value': q,
                    'label': self._get_quality_label(q),
                    'available': True,
                    'filesize': qualities[q]['filesize']
                })
        
        return result
    
    def _height_to_quality(self, height):
        """Convert height to quality label"""
        if height >= 4320:
            return '8k'
        elif height >= 2160:
            return '4k'
        elif height >= 1440:
            return '2k'
        elif height >= 1080:
            return '1080p'
        elif height >= 720:
            return '720p'
        elif height >= 480:
            return '480p'
        elif height >= 360:
            return '360p'
        elif height >= 240:
            return '240p'
        elif height >= 144:
            return '144p'
        return None
    
    def _get_quality_label(self, quality):
        """Get display label for quality"""
        labels = {
            '8k': '8K Ultra HD (4320p)',
            '4k': '4K Ultra HD (2160p)',
            '2k': '2K QHD (1440p)',
            '1080p': 'Full HD (1080p)',
            '720p': 'HD (720p)',
            '480p': 'SD (480p)',
            '360p': '360p',
            '240p': '240p',
            '144p': '144p'
        }
        return labels.get(quality, quality)
    
    def _get_available_formats(self, info, content_type):
        """Get available formats based on content type"""
        
        if content_type == 'photo':
            return {
                'type': 'photo',
                'formats': [
                    {'value': 'jpg', 'label': 'JPG (Recommended)', 'available': True},
                    {'value': 'png', 'label': 'PNG (High Quality)', 'available': True},
                    {'value': 'webp', 'label': 'WebP', 'available': True},
                ]
            }
        
        if content_type == 'audio':
            return {
                'type': 'audio',
                'formats': [
                    {'value': 'mp3', 'label': 'MP3 (Recommended)', 'available': True},
                    {'value': 'm4a', 'label': 'M4A', 'available': True},
                    {'value': 'wav', 'label': 'WAV (Lossless)', 'available': True},
                ]
            }
        
        # Video - return both video and audio options
        return {
            'type': 'video',
            'video_formats': [
                {'value': 'mp4', 'label': 'MP4 (Recommended)', 'available': True},
                {'value': 'webm', 'label': 'WebM', 'available': True},
                {'value': 'mkv', 'label': 'MKV', 'available': True},
            ],
            'audio_formats': [
                {'value': 'mp3', 'label': 'MP3 (Recommended)', 'available': True},
                {'value': 'm4a', 'label': 'M4A', 'available': True},
                {'value': 'wav', 'label': 'WAV', 'available': True},
            ]
        }
    
    def download(self, url, quality='highest', format_type='mp4', download_type='video'):
        """Download media from URL"""
        
        ydl_opts = self._get_download_options(quality, format_type, download_type)
        ydl_opts['outtmpl'] = os.path.join(self.download_path, '%(title)s.%(ext)s')
        ydl_opts['restrictfilenames'] = True
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                # Handle audio extraction filename
                if download_type == 'audio':
                    base = os.path.splitext(filename)[0]
                    filename = f"{base}.{format_type}"
                
                # Check if file exists and has content
                if os.path.exists(filename):
                    filesize = os.path.getsize(filename)
                    if filesize == 0:
                        return {'success': False, 'error': 'Downloaded file is empty. Try a different quality.'}
                    
                    return {
                        'success': True,
                        'title': info.get('title'),
                        'filename': os.path.basename(filename),
                        'filepath': filename,
                        'platform': info.get('extractor_key'),
                        'filesize': filesize,
                        'filesize_readable': self._format_filesize(filesize)
                    }
                else:
                    # Try to find the actual file
                    base = os.path.splitext(filename)[0]
                    for ext in ['mp4', 'webm', 'mkv', 'mp3', 'm4a', 'wav', 'jpg', 'png', 'webp']:
                        test_file = f"{base}.{ext}"
                        if os.path.exists(test_file):
                            filesize = os.path.getsize(test_file)
                            return {
                                'success': True,
                                'title': info.get('title'),
                                'filename': os.path.basename(test_file),
                                'filepath': test_file,
                                'platform': info.get('extractor_key'),
                                'filesize': filesize,
                                'filesize_readable': self._format_filesize(filesize)
                            }
                    
                    return {'success': False, 'error': 'Could not find downloaded file.'}
                    
        except Exception as e:
            error_msg = str(e)
            if 'unavailable' in error_msg.lower():
                return {'success': False, 'error': 'This quality is not available. Please try a lower quality.'}
            return {'success': False, 'error': error_msg}
    
    def _get_download_options(self, quality, format_type, download_type):
        """Get yt-dlp options based on download type"""
        
        # Photo download
        if download_type == 'photo':
            return {
                'quiet': True,
                'no_warnings': True,
            }
        
        # Audio only download
        if download_type == 'audio':
            return {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': format_type,
                    'preferredquality': '320',
                }],
                'quiet': False,
            }
        
        # Video download with specific quality
        quality_map = {
            '8k': 4320,
            '4k': 2160,
            '2k': 1440,
            '1080p': 1080,
            '720p': 720,
            '480p': 480,
            '360p': 360,
            '240p': 240,
            '144p': 144,
        }
        
        if quality in quality_map:
            height = quality_map[quality]
            format_string = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]'
        else:
            format_string = 'bestvideo+bestaudio/best'
        
        return {
            'format': format_string,
            'merge_output_format': format_type,
            'quiet': False,
        }
    
    def _format_filesize(self, size):
        """Format filesize to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


if __name__ == "__main__":
    downloader = SocialDownloader()
    print("Downloader ready!")