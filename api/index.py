import os
import sys
from urllib.parse import unquote, urlparse

# Add root directory to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app

class VercelPathFixMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        # Prefer original requested URI headers
        raw_uri = (
            environ.get('RAW_URI') or
            environ.get('REQUEST_URI') or
            environ.get('HTTP_X_FORWARDED_URI') or
            environ.get('HTTP_X_VERCEL_PATH') or
            ''
        )
        
        if raw_uri:
            parsed = urlparse(raw_uri)
            path = parsed.path
        else:
            path = environ.get('PATH_INFO', '')

        path = unquote(path or '')

        # Check regex match parameter from Vercel rewrite if path is pointing to entrypoint
        if not path or path in ('/api/index', '/api/index.py', '/api', '/api/', '/'):
            route_matches = environ.get('HTTP_X_NOW_ROUTE_MATCHES', '')
            if route_matches:
                for part in route_matches.split('&'):
                    if part.startswith('1='):
                        captured = unquote(part[2:])
                        if captured:
                            path = captured if captured.startswith('/') else '/' + captured
                        break

        # Normalize entrypoint prefixes
        if path.startswith('/api/index.py'):
            path = path[len('/api/index.py'):]
        elif path.startswith('/api/index'):
            path = path[len('/api/index'):]
        elif path.startswith('/api'):
            path = path[len('/api'):]

        if not path:
            path = '/'

        environ['PATH_INFO'] = path
        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathFixMiddleware(app.wsgi_app)
handler = app


