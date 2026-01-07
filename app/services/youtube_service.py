import asyncio
import os
import uuid
from typing import Optional
import yt_dlp

from app.core.config import settings

class YouTubeService:
    def __init__(self):
        self.download_path = settings.DOWNLOAD_PATH
        os.makedirs(self.download_path, exist_ok=True)

    async def get_video_info(self, url: str) -> dict:
        """Get video metadata without downloading"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }

        loop = asyncio.get_event_loop()

        def extract():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)

        info = await loop.run_in_executor(None, extract)

        return {
            'id': info.get('id'),
            'title': info.get('title'),
            'artist': info.get('uploader') or info.get('artist') or 'Unknown',
            'thumbnail': info.get('thumbnail'),
            'duration': info.get('duration', 0),
            'view_count': info.get('view_count', 0),
        }

    async def search(self, query: str, limit: int = 20) -> list:
        """Search YouTube videos"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'default_search': 'ytsearch',
        }

        loop = asyncio.get_event_loop()

        def search_videos():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(f"ytsearch{limit}:{query}", download=False)

        results = await loop.run_in_executor(None, search_videos)

        videos = []
        for entry in results.get('entries', []):
            if entry:
                videos.append({
                    'id': entry.get('id'),
                    'title': entry.get('title'),
                    'artist': entry.get('uploader') or 'Unknown',
                    'thumbnail': entry.get('thumbnail') or f"https://i.ytimg.com/vi/{entry.get('id')}/hqdefault.jpg",
                    'duration': entry.get('duration', 0),
                })

        return videos

    async def download_audio(
        self,
        video_id: str,
        quality: str = "128",
        progress_callback: Optional[callable] = None,
    ) -> dict:
        """Download and convert video to MP3"""

        output_filename = f"{uuid.uuid4().hex}"
        output_path = os.path.join(self.download_path, output_filename)

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{output_path}.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality,
            }, {
                'key': 'FFmpegMetadata',
                'add_metadata': True,
            }, {
                'key': 'EmbedThumbnail',
            }],
            'writethumbnail': True,
            'quiet': True,
            'no_warnings': True,
        }

        if progress_callback:
            def hook(d):
                if d['status'] == 'downloading':
                    total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                    downloaded = d.get('downloaded_bytes', 0)
                    if total > 0:
                        progress_callback(downloaded / total)
            ydl_opts['progress_hooks'] = [hook]

        loop = asyncio.get_event_loop()

        def download():
            url = f"https://www.youtube.com/watch?v={video_id}"
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return info

        info = await loop.run_in_executor(None, download)

        final_path = f"{output_path}.mp3"
        file_size = os.path.getsize(final_path) if os.path.exists(final_path) else 0

        return {
            'file_path': final_path,
            'file_size': file_size,
            'title': info.get('title'),
            'artist': info.get('uploader') or info.get('artist'),
            'duration': info.get('duration', 0),
        }

    async def get_playlist(self, playlist_url: str) -> list:
        """Get all videos from a playlist"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }

        loop = asyncio.get_event_loop()

        def extract_playlist():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(playlist_url, download=False)

        results = await loop.run_in_executor(None, extract_playlist)

        videos = []
        for entry in results.get('entries', []):
            if entry:
                videos.append({
                    'id': entry.get('id'),
                    'title': entry.get('title'),
                    'artist': entry.get('uploader') or 'Unknown',
                    'duration': entry.get('duration', 0),
                })

        return videos

youtube_service = YouTubeService()
