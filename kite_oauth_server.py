#!/usr/bin/env python3
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from kiteconnect import KiteConnect

API_KEY    = "wye4akybc8q7bf6j"
API_SECRET = "yayjdjidkw87mpzu8j7el41nq33zj7aa"
PORT       = 8080  # Redirect URL must be http://localhost:8080

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse ?request_token=...&checksum=...
        qs = parse_qs(urlparse(self.path).query)
        if "request_token" in qs:
            token = qs["request_token"][0]

            # Send HTTP response
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h1>Token received—check console.</h1></body></html>"
            )

            # Exchange for access token
            kite = KiteConnect(api_key=API_KEY)
            data = kite.generate_session(token, api_secret=API_SECRET)
            access_token = data["access_token"]
            print("\n=== ACCESS TOKEN ===")
            print(access_token)
            print("====================\n")

            # Shut down the server
            threading.Thread(target=httpd.shutdown).start()
        else:
            self.send_error(400, "Missing request_token")

if __name__ == "__main__":
    httpd = HTTPServer(("localhost", PORT), Handler)
    print(f"1) In your Kite App, set Redirect URL → http://localhost:{PORT}")
    print("2) Run this server, then open the login URL:")
    print(KiteConnect(api_key=API_KEY).login_url())
    print("3) After login, this server will capture and print your access_token.\n")
    httpd.serve_forever()
