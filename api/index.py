import os
import sys
from urllib.parse import unquote, urlparse, parse_qs, urlencode

# Add root directory to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app

class VercelPathFixMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        query_string = environ.get('QUERY_STRING', '')
        resolved_path = None

        # 1. Check if __vercel_path is passed in query string from rewrite
        if '__vercel_path=' in query_string:
            qs_dict = parse_qs(query_string, keep_blank_values=True)
            if '__vercel_path' in qs_dict:
                val = qs_dict.pop('__vercel_path')[0]
                if val:
                    val = unquote(val)
                    resolved_path = val if val.startswith('/') else '/' + val
                else:
                    resolved_path = '/'
                # Clean up query string so Flask views receive original parameters
                environ['QUERY_STRING'] = urlencode(qs_dict, doseq=True)

        # 2. Fallback to RAW_URI / REQUEST_URI / HTTP_X_FORWARDED_URI / PATH_INFO
        if not resolved_path:
            raw_uri = (
                environ.get('RAW_URI') or
                environ.get('REQUEST_URI') or
                environ.get('HTTP_X_FORWARDED_URI') or
                environ.get('HTTP_X_VERCEL_PATH') or
                ''
            )
            if raw_uri:
                resolved_path = urlparse(raw_uri).path
            else:
                resolved_path = environ.get('PATH_INFO', '')

        resolved_path = unquote(resolved_path or '/')

        # Normalize prefix
        if resolved_path.startswith('/api/index.py'):
            resolved_path = resolved_path[len('/api/index.py'):]
        elif resolved_path.startswith('/api/index'):
            resolved_path = resolved_path[len('/api/index'):]
        elif resolved_path.startswith('/api'):
            resolved_path = resolved_path[len('/api'):]

        if not resolved_path:
            resolved_path = '/'

        environ['PATH_INFO'] = resolved_path
        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathFixMiddleware(app.wsgi_app)
handler = app



