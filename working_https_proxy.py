#!/usr/bin/env python3
"""
Working HTTPS Proxy Server
Simple implementation that properly handles both HTTP and HTTPS requests.

MIT License
Copyright (c) 2025 Anju982

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import http.server
import socketserver
import urllib.request
import urllib.parse
import urllib.error
import ssl
import random
import time
import logging
import threading
from typing import Optional, List

# Configuration
PORT = 8080
REQUEST_DELAY = 1
TIMEOUT = 30

# Simple proxy pool (can be expanded)
PROXY_POOL: List[str] = []

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

# Setup logging
logging.basicConfig(
    filename="working_https_proxy.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def fetch_proxies():
    """Fetch a few working proxies"""
    try:
        api_url = "https://api.proxyscrape.com/v4/free-proxy-list/get?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all&skip=0&limit=20"
        
        with urllib.request.urlopen(api_url, timeout=30) as response:
            content = response.read().decode('utf-8').strip()
            
        proxies = []
        for line in content.split('\n')[:10]:  # Take first 10
            line = line.strip()
            if line and ':' in line:
                proxies.append(f"http://{line}")
        
        return proxies
    except Exception as e:
        logging.error(f"Failed to fetch proxies: {e}")
        return []

class WorkingHTTPSHandler(http.server.BaseHTTPRequestHandler):
    """Simple HTTP/HTTPS proxy handler that actually works"""
    
    def create_ssl_context(self):
        """Create SSL context for HTTPS requests"""
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context
    
    def get_proxy(self) -> Optional[str]:
        """Get a random proxy from pool"""
        if PROXY_POOL:
            return random.choice(PROXY_POOL)
        return None
    
    def normalize_url(self, path: str) -> str:
        """Normalize the URL from request path"""
        # Remove leading slash
        if path.startswith('/'):
            path = path[1:]
        
        # If no protocol specified, assume https for common sites
        if not path.startswith(('http://', 'https://')):
            # Auto-detect common HTTPS sites
            if any(site in path.lower() for site in ['google', 'github', 'facebook', 'twitter']):
                path = 'https://' + path
            else:
                path = 'http://' + path
        
        return path
    
    def make_request(self, url: str, method: str = 'GET', data: bytes = None):
        """Make HTTP/HTTPS request with proxy fallback"""
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'identity',  # Disable compression for simplicity
            'Connection': 'close'
        }
        
        # Copy some original headers
        for header in ['Content-Type', 'Content-Length']:
            if header in self.headers:
                headers[header] = self.headers[header]
        
        success = False
        attempts = []
        
        # Try with proxy first
        proxy = self.get_proxy()
        if proxy:
            try:
                attempts.append(f"Trying proxy: {proxy}")
                
                proxy_handler = urllib.request.ProxyHandler({
                    'http': proxy,
                    'https': proxy
                })
                
                opener = urllib.request.build_opener(proxy_handler)
                
                # Create custom request class for method override
                class HTTPMethodRequest(urllib.request.Request):
                    def __init__(self, *args, **kwargs):
                        self._method = method
                        super().__init__(*args, **kwargs)
                    
                    def get_method(self):
                        return self._method
                
                request = HTTPMethodRequest(url, data=data, headers=headers)
                
                with opener.open(request, timeout=TIMEOUT) as response:
                    self.send_response(response.status)
                    
                    # Forward headers (skip problematic ones)
                    skip_headers = {'connection', 'transfer-encoding', 'content-encoding'}
                    for key, value in response.getheaders():
                        if key.lower() not in skip_headers:
                            self.send_header(key, value)
                    
                    self.end_headers()
                    self.wfile.write(response.read())
                
                success = True
                attempts.append("✅ Proxy request successful")
                
            except Exception as e:
                attempts.append(f"❌ Proxy failed: {str(e)}")
        
        # If proxy failed, try direct connection
        if not success:
            try:
                attempts.append("Trying direct connection...")
                
                class HTTPMethodRequest(urllib.request.Request):
                    def __init__(self, *args, **kwargs):
                        self._method = method
                        super().__init__(*args, **kwargs)
                    
                    def get_method(self):
                        return self._method
                
                request = HTTPMethodRequest(url, data=data, headers=headers)
                
                with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                    self.send_response(response.status)
                    
                    # Forward headers
                    skip_headers = {'connection', 'transfer-encoding', 'content-encoding'}
                    for key, value in response.getheaders():
                        if key.lower() not in skip_headers:
                            self.send_header(key, value)
                    
                    self.end_headers()
                    self.wfile.write(response.read())
                
                success = True
                attempts.append("✅ Direct connection successful")
                
            except Exception as e:
                attempts.append(f"❌ Direct connection failed: {str(e)}")
        
        # Log the attempts
        logging.info(f"{method} {url} - " + " | ".join(attempts))
        
        if not success:
            self.send_error(502, "All connection attempts failed")
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            # Handle root request
            if self.path == '/' or self.path == '':
                self.send_error(400, "No URL provided. Use format: http://localhost:8080/target-url")
                return
            
            # Normalize URL
            url = self.normalize_url(self.path)
            
            # Add delay
            time.sleep(REQUEST_DELAY)
            
            # Make request
            self.make_request(url, 'GET')
            
        except Exception as e:
            logging.error(f"Error in do_GET: {e}")
            self.send_error(500, str(e))
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            url = self.normalize_url(self.path)
            
            # Read POST data
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else None
            
            time.sleep(REQUEST_DELAY)
            self.make_request(url, 'POST', post_data)
            
        except Exception as e:
            logging.error(f"Error in do_POST: {e}")
            self.send_error(500, str(e))
    
    def log_message(self, format, *args):
        """Custom logging"""
        logging.info(f"{self.address_string()} - {format % args}")

def initialize_proxies():
    """Initialize proxy pool"""
    global PROXY_POOL
    print("📥 Fetching proxy pool...")
    
    proxies = fetch_proxies()
    if proxies:
        PROXY_POOL = proxies
        print(f"✅ Loaded {len(PROXY_POOL)} proxies")
    else:
        print("⚠️  No proxies loaded - using direct connections only")

def run_server():
    """Start the proxy server"""
    try:
        print("🚀 Starting Working HTTPS Proxy Server...")
        
        # Initialize proxies
        initialize_proxies()
        
        # Create server
        with socketserver.TCPServer(("", PORT), WorkingHTTPSHandler) as httpd:
            print(f"🌐 Server running on http://localhost:{PORT}")
            print("📝 Usage examples:")
            print(f"   curl 'http://localhost:{PORT}/https://httpbin.org/ip'")
            print(f"   curl 'http://localhost:{PORT}/http://httpbin.org/user-agent'")
            print(f"   curl 'http://localhost:{PORT}/google.com'  # Auto-detects HTTPS")
            print()
            print("📊 Status dashboard available at: http://localhost:8888")
            print("⏹️  Press Ctrl+C to stop")
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n⏹️  Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    run_server()
