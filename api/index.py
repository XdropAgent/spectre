import sys
import os

# Add parent directory to path so we can import from web/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from web.app import app

# Vercel handler
def handler(request, response):
    return app(request, response)
