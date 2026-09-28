"""Serve only the explorer and stage resources on localhost and open the explorer."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from posixpath import normpath
from urllib.parse import unquote, urlsplit
import webbrowser


class StagesHandler(SimpleHTTPRequestHandler):
    # The page lives at the repo root beside local-only Strava files; expose nothing else.
    def send_head(self):
        path = normpath(unquote(urlsplit(self.path).path))
        if path != '/stages.html' and not path.startswith('/Resources/Stages/'):
            self.send_error(404)
            return None
        return super().send_head()


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[2]
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(StagesHandler, directory=str(root)))
    webbrowser.open(f'http://127.0.0.1:{server.server_port}/stages.html')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
