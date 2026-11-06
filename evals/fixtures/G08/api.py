from http.server import BaseHTTPRequestHandler
import json

class ExportHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != '/export':
            self.send_error(404)
            return
        data = json.dumps({'rows': [{'id': 1}]}).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    def log_message(self, *args): pass
