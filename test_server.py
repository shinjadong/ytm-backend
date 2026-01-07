#!/usr/bin/env python3
"""Lightweight test server for YTM API"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import subprocess
import os
import urllib.parse

class YTMHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == '/':
            self._send_json({'message': 'YTM API v1.0', 'status': 'ok'})

        elif path == '/api/videos/info':
            url = query.get('url', [''])[0]
            if not url:
                self._send_json({'error': 'URL required'}, 400)
                return

            try:
                result = subprocess.run(
                    ['yt-dlp', '-j', '--no-download', url],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    info = json.loads(result.stdout)
                    self._send_json({
                        'id': info.get('id'),
                        'title': info.get('title'),
                        'artist': info.get('uploader', 'Unknown'),
                        'thumbnail': info.get('thumbnail'),
                        'duration': info.get('duration', 0),
                    })
                else:
                    self._send_json({'error': result.stderr}, 400)
            except Exception as e:
                self._send_json({'error': str(e)}, 500)

        elif path == '/api/videos/search':
            q = query.get('q', [''])[0]
            limit = int(query.get('limit', ['10'])[0])
            if not q:
                self._send_json({'error': 'Query required'}, 400)
                return

            try:
                result = subprocess.run(
                    ['yt-dlp', f'ytsearch{limit}:{q}', '-j', '--flat-playlist', '--no-download'],
                    capture_output=True, text=True, timeout=30
                )
                videos = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        info = json.loads(line)
                        videos.append({
                            'id': info.get('id'),
                            'title': info.get('title'),
                            'artist': info.get('uploader', 'Unknown'),
                            'duration': info.get('duration', 0),
                        })
                self._send_json({'videos': videos, 'count': len(videos)})
            except Exception as e:
                self._send_json({'error': str(e)}, 500)

        elif path.startswith('/api/download'):
            video_id = query.get('id', [''])[0]
            if not video_id:
                self._send_json({'error': 'Video ID required'}, 400)
                return

            output_dir = '/storage/emulated/0/Music/YTM'
            os.makedirs(output_dir, exist_ok=True)

            try:
                # Get info first
                info_result = subprocess.run(
                    ['yt-dlp', '-j', '--no-download', f'https://youtube.com/watch?v={video_id}'],
                    capture_output=True, text=True, timeout=30
                )
                info = json.loads(info_result.stdout)
                title = info.get('title', video_id)

                self._send_json({
                    'status': 'started',
                    'video_id': video_id,
                    'title': title,
                    'message': f'Downloading to {output_dir}'
                })

            except Exception as e:
                self._send_json({'error': str(e)}, 500)

        else:
            self._send_json({'error': 'Not found'}, 404)

    def do_POST(self):
        if self.path == '/api/download':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body) if body else {}

            video_id = data.get('video_id')
            if not video_id:
                self._send_json({'error': 'video_id required'}, 400)
                return

            output_dir = '/storage/emulated/0/Music/YTM'
            os.makedirs(output_dir, exist_ok=True)

            self._send_json({
                'status': 'queued',
                'video_id': video_id,
                'output_dir': output_dir,
            })
        else:
            self._send_json({'error': 'Not found'}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        print(f"[API] {args[0]}")

if __name__ == '__main__':
    port = 8000
    server = HTTPServer(('0.0.0.0', port), YTMHandler)
    print(f'YTM API Server running on http://localhost:{port}')
    print('Endpoints:')
    print('  GET  /api/videos/info?url=<youtube_url>')
    print('  GET  /api/videos/search?q=<query>')
    print('  GET  /api/download?id=<video_id>')
    print('  POST /api/download {"video_id": "xxx"}')
    server.serve_forever()
