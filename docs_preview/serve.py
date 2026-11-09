# Local preview server that never caches, so edits show up on a normal refresh.
# Run from this folder:  python3 serve.py   then open http://localhost:8000
import http.server, functools, os

class NoCache(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, must-revalidate')
        super().end_headers()

handler = functools.partial(NoCache, directory=os.path.dirname(os.path.abspath(__file__)))
print('Serving http://localhost:8000 (Ctrl+C to stop)')
http.server.ThreadingHTTPServer(('', 8000), handler).serve_forever()
