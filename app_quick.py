#!/usr/bin/env python3
"""
Quick start proxy server without proxy validation for faster testing.
This version skips proxy validation and uses all fetched proxies.
"""

import http.server
import socketserver
import urllib.request
import urllib.parse
import random
import time
import logging
import threading
from typing import Optional, Dict, List
from urllib.error import URLError, HTTPError

# Configuration
PORT = 8081  # Different port to avoid conflicts
REQUEST_DELAY = 1  # seconds
TIMEOUT = 30  # seconds
PROXY_REFRESH_INTERVAL = 1800  # 30 minutes in seconds
PROXY_API_URL = "https://api.proxyscrape.com/v4/free-proxy-list/get?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all&skip=0&limit=100"

# Global proxy pool - will be populated from API
PROXY_POOL: List[str] = []

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
]

# Improved logging configuration
logging.basicConfig(
    filename="proxy_quick.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def fetch_proxies_from_api() -> List[str]:
    """Fetch proxies from ProxyScrape API - quick version."""
    try:
        logging.info("Fetching proxies from API...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        request = urllib.request.Request(PROXY_API_URL, headers=headers)
        
        with urllib.request.urlopen(request, timeout=30) as response:
            content = response.read().decode('utf-8').strip()
            
        proxies = []
        for line in content.split('\n'):
            line = line.strip()
            if line and ':' in line:
                proxy = f"http://{line}"
                proxies.append(proxy)
        
        logging.info(f"Successfully fetched {len(proxies)} proxies from API")
        return proxies
        
    except Exception as e:
        logging.error(f"Failed to fetch proxies from API: {e}")
        return []

def update_proxy_pool():
    """Update the global proxy pool with fresh proxies - no validation."""
    global PROXY_POOL
    
    new_proxies = fetch_proxies_from_api()
    if new_proxies:
        PROXY_POOL = new_proxies
        logging.info(f"Updated proxy pool with {len(PROXY_POOL)} proxies (no validation)")
    else:
        logging.warning("Failed to update proxy pool - keeping existing proxies")

class QuickProxyHandler(http.server.BaseHTTPRequestHandler):
    timeout = TIMEOUT
    
    def get_random_proxy(self) -> Optional[str]:
        """Get a random proxy from the pool."""
        if not PROXY_POOL:
            return None
        return random.choice(PROXY_POOL)
    
    def get_random_user_agent(self) -> str:
        """Get a random user agent from the list."""
        return random.choice(USER_AGENTS)
    
    def validate_url(self, url: str) -> Optional[str]:
        """Validate and normalize the URL."""
        try:
            parsed = urllib.parse.urlparse(url)
            if not parsed.scheme:
                url = "http://" + url
            return url
        except Exception as e:
            logging.error(f"Invalid URL: {url}, Error: {e}")
            return None
    
    def forward_request(self, url: str, headers: Dict[str, str]):
        """Forward the request with simple proxy rotation."""
        try:
            proxy = self.get_random_proxy()
            
            if proxy:
                logging.info(f"Using proxy {proxy} for {url}")
                proxy_handler = urllib.request.ProxyHandler({"http": proxy, "https": proxy})
                opener = urllib.request.build_opener(proxy_handler)
            else:
                logging.warning("No proxy available, using direct connection")
                opener = urllib.request.build_opener()
            
            request = urllib.request.Request(url, headers=headers)
            
            with opener.open(request, timeout=self.timeout) as response:
                self.send_response(response.status)
                for key, value in response.getheaders():
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(response.read())
                
            logging.info(f"Successfully forwarded request: {url}")
            
        except Exception as e:
            logging.error(f"Error forwarding request: {str(e)} - {url}")
            self.send_error(500, str(e))

    def do_GET(self):
        """Handle GET requests."""
        try:
            url = self.path[1:]
            url = self.validate_url(url)
            if not url:
                self.send_error(400, "Invalid URL")
                return
            
            time.sleep(REQUEST_DELAY)
            
            headers = {
                "User-Agent": self.get_random_user_agent(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
            
            self.forward_request(url, headers)
            
        except Exception as e:
            logging.error(f"Error in do_GET: {str(e)}")
            self.send_error(500, str(e))

def run_quick_server():
    """Run the quick proxy server."""
    try:
        print("Quick proxy server - fetching proxies...")
        update_proxy_pool()
        
        print(f"Loaded {len(PROXY_POOL)} proxies (no validation)")
        
        with socketserver.TCPServer(("", PORT), QuickProxyHandler) as httpd:
            print(f"Quick proxy server running on port {PORT}")
            logging.info(f"Quick server started on port {PORT}")
            httpd.serve_forever()
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_quick_server()
