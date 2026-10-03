#!/usr/bin/env python3
"""
Custom HTTP server with Range Header (HTTP 206 Partial Content) support.
Optimized for 4K video streaming and instant timeline seeking.
"""

import os
import sys
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class RangeRequestHandler(BaseHTTPRequestHandler):
    def translate_path(self, path):
        # Normalize and map path
        path = path.split('?', 1)[0].split('#', 1)[0]
        rel_path = path.lstrip('/')
        if not rel_path:
            rel_path = 'index.html'
        full_path = os.path.normpath(os.path.join(DIRECTORY, rel_path))
        if os.path.isdir(full_path):
            full_path = os.path.join(full_path, 'index.html')
        return full_path

    def do_HEAD(self):
        self.send_file(head_only=True)

    def do_GET(self):
        self.send_file(head_only=False)

    def send_file(self, head_only=False):
        filepath = self.translate_path(self.path)
        if not os.path.exists(filepath) or not os.path.isfile(filepath):
            self.send_error(404, f"File Not Found: {self.path}")
            return

        file_size = os.path.getsize(filepath)
        mime_type, _ = mimetypes.guess_type(filepath)
        if not mime_type:
            if filepath.endswith('.vtt'):
                mime_type = 'text/vtt'
            else:
                mime_type = 'application/octet-stream'

        range_header = self.headers.get('Range')

        if range_header and range_header.startswith('bytes='):
            try:
                ranges = range_header.replace('bytes=', '').split('-')
                start = int(ranges[0]) if ranges[0] else 0
                end = int(ranges[1]) if ranges[1] else file_size - 1
                end = min(end, file_size - 1)
                length = end - start + 1

                self.send_response(206)
                self.send_header('Content-Type', mime_type)
                self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
                self.send_header('Content-Length', str(length))
                self.send_header('Accept-Ranges', 'bytes')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()

                if not head_only:
                    with open(filepath, 'rb') as f:
                        f.seek(start)
                        remaining = length
                        chunk_size = 64 * 1024
                        while remaining > 0:
                            chunk = f.read(min(remaining, chunk_size))
                            if not chunk:
                                break
                            self.wfile.write(chunk)
                            remaining -= len(chunk)
                return
            except (ConnectionResetError, BrokenPipeError):
                return
            except Exception as e:
                pass

        # Standard 200 OK
        try:
            self.send_response(200)
            self.send_header('Content-Type', mime_type)
            self.send_header('Content-Length', str(file_size))
            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()

            if not head_only:
                with open(filepath, 'rb') as f:
                    chunk_size = 64 * 1024
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
        except (ConnectionResetError, BrokenPipeError):
            pass

def run():
    port = PORT
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    server = HTTPServer(('0.0.0.0', port), RangeRequestHandler)
    print(f"General Intelligence Company server running at http://localhost:{port}/")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == '__main__':
    run()
