#!/usr/bin/env python3
"""Serve the demo website on http://localhost:5173 and open it in the browser.

    python serve.py            # then press Ctrl+C to stop
    python serve.py --port 8080
"""

import argparse
import functools
import http.server
import threading
import webbrowser
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=5173)
args = parser.parse_args()

site = Path(__file__).parent / "website"
handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(site))
url = f"http://localhost:{args.port}"

with http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
    print(f"Serving {site} at {url}  (Ctrl+C to stop)")
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
