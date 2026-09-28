"""Serve only the stage resources on localhost and open the explorer."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import webbrowser

if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(SimpleHTTPRequestHandler, directory=str(root)))
    webbrowser.open(f'http://127.0.0.1:{server.server_port}/Desert_Dash.html')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
