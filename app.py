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
PORT = 8080
REQUEST_DELAY = 1  # seconds
TIMEOUT = 30  # seconds
PROXY_REFRESH_INTERVAL = 1800  # 30 minutes in seconds
PROXY_API_URL = "https://api.proxyscrape.com/v4/free-proxy-list/get?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all&skip=0&limit=500"

# Global proxy pool - will be populated from API
PROXY_POOL: List[str] = []

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
]

# Improved logging configuration
logging.basicConfig(
    filename="proxy.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def fetch_proxies_from_api() -> List[str]:
    """Fetch proxies from ProxyScrape API."""
    try:
        logging.info("Fetching proxies from API...")
        
        # Create request with headers to avoid blocking
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        request = urllib.request.Request(PROXY_API_URL, headers=headers)
        
        with urllib.request.urlopen(request, timeout=30) as response:
            content = response.read().decode('utf-8').strip()
            
        # Parse the response - should be one proxy per line in format ip:port
        proxies = []
        for line in content.split('\n'):
            line = line.strip()
            if line and ':' in line:
                # Format as http://ip:port
                proxy = f"http://{line}"
                proxies.append(proxy)
        
        logging.info(f"Successfully fetched {len(proxies)} proxies from API")
        return proxies
        
    except Exception as e:
        logging.error(f"Failed to fetch proxies from API: {e}")
        return []

def validate_proxy(proxy: str, test_url: str = "http://httpbin.org/ip") -> bool:
    """Test if a proxy is working by making a simple request."""
    try:
        proxy_handler = urllib.request.ProxyHandler({"http": proxy, "https": proxy})
        opener = urllib.request.build_opener(proxy_handler)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        request = urllib.request.Request(test_url, headers=headers)
        
        with opener.open(request, timeout=10) as response:
            if response.status == 200:
                return True
        return False
    except Exception:
        return False

def get_working_proxies(proxy_list: List[str], max_to_test: int = 50) -> List[str]:
    """Filter out non-working proxies by testing them."""
    working_proxies = []
    tested = 0
    
    logging.info(f"Testing up to {max_to_test} proxies for functionality...")
    
    for proxy in proxy_list:
        if tested >= max_to_test:
            break
            
        if validate_proxy(proxy):
            working_proxies.append(proxy)
            logging.info(f"Proxy {proxy} is working")
        
        tested += 1
        
        # Add small delay between tests to avoid overwhelming
        time.sleep(0.1)
    
    logging.info(f"Found {len(working_proxies)} working proxies out of {tested} tested")
    return working_proxies

def update_proxy_pool():
    """Update the global proxy pool with fresh proxies."""
    global PROXY_POOL
    
    new_proxies = fetch_proxies_from_api()
    if new_proxies:
        # Test a subset of proxies to find working ones
        working_proxies = get_working_proxies(new_proxies, max_to_test=100)
        
        if working_proxies:
            PROXY_POOL = working_proxies
            logging.info(f"Updated proxy pool with {len(PROXY_POOL)} working proxies")
        else:
            # If no working proxies found, keep some untested ones as fallback
            PROXY_POOL = new_proxies[:50]  # Keep first 50 as fallback
            logging.warning("No working proxies found during validation, using untested proxies as fallback")
    else:
        logging.warning("Failed to update proxy pool - keeping existing proxies")

def start_proxy_refresh_timer():
    """Start a timer to refresh proxies periodically."""
    def refresh_loop():
        while True:
            time.sleep(PROXY_REFRESH_INTERVAL)
            logging.info("Refreshing proxy pool...")
            update_proxy_pool()
    
    # Start the refresh loop in a daemon thread
    refresh_thread = threading.Thread(target=refresh_loop, daemon=True)
    refresh_thread.start()
    logging.info(f"Started proxy refresh timer - will refresh every {PROXY_REFRESH_INTERVAL/60} minutes")

class ProxyHandler(http.server.BaseHTTPRequestHandler):
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
        """Forward the request to the target server with proxy rotation and fallback."""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                if not PROXY_POOL:
                    # Fallback to direct connection if no proxies available
                    logging.warning("No proxies available, attempting direct connection")
                    request = urllib.request.Request(url, headers=headers)
                    with urllib.request.urlopen(request, timeout=self.timeout) as response:
                        self.send_response(response.status)
                        for key, value in response.getheaders():
                            self.send_header(key, value)
                        self.end_headers()
                        self.wfile.write(response.read())
                    logging.info(f"Successfully forwarded request directly: {url}")
                    return
                
                proxy = self.get_random_proxy()
                if not proxy:
                    # Fallback to direct connection if no proxy available
                    logging.warning("No proxy available, attempting direct connection")
                    request = urllib.request.Request(url, headers=headers)
                    with urllib.request.urlopen(request, timeout=self.timeout) as response:
                        self.send_response(response.status)
                        for key, value in response.getheaders():
                            self.send_header(key, value)
                        self.end_headers()
                        self.wfile.write(response.read())
                    logging.info(f"Successfully forwarded request directly: {url}")
                    return
                
                logging.info(f"Attempt {attempt + 1}: Using proxy {proxy} for {url}")
                
                proxy_handler = urllib.request.ProxyHandler({"http": proxy, "https": proxy})
                opener = urllib.request.build_opener(proxy_handler)
                
                request = urllib.request.Request(url, headers=headers)
                
                with opener.open(request, timeout=self.timeout) as response:
                    self.send_response(response.status)
                    for key, value in response.getheaders():
                        self.send_header(key, value)
                    self.end_headers()
                    self.wfile.write(response.read())
                    
                logging.info(f"Successfully forwarded request: {url} via {proxy}")
                return  # Success, exit the retry loop
                
            except HTTPError as e:
                logging.error(f"HTTP Error with proxy {proxy if 'proxy' in locals() else 'direct'}: {e.code} - {url}")
                if attempt == max_retries - 1:  # Last attempt
                    self.send_error(e.code, str(e))
                # Continue to next attempt
                
            except URLError as e:
                logging.error(f"URL Error with proxy {proxy if 'proxy' in locals() else 'direct'}: {str(e)} - {url}")
                if attempt == max_retries - 1:  # Last attempt
                    self.send_error(504, str(e))
                # Continue to next attempt
                
            except TimeoutError:
                logging.error(f"Timeout Error with proxy {proxy if 'proxy' in locals() else 'direct'}: {url}")
                if attempt == max_retries - 1:  # Last attempt
                    self.send_error(504, "Request timed out")
                # Continue to next attempt
                
            except Exception as e:
                logging.error(f"Error with proxy {proxy if 'proxy' in locals() else 'direct'}: {str(e)} - {url}")
                if attempt == max_retries - 1:  # Last attempt
                    self.send_error(500, str(e))
                # Continue to next attempt
            
            # Small delay between retries
            time.sleep(1)

    def do_GET(self):
        """Handle GET requests."""
        try:
            # Remove leading slash and validate URL
            url = self.path[1:]
            url = self.validate_url(url)
            if not url:
                self.send_error(400, "Invalid URL")
                return
            
            # Add request delay
            time.sleep(REQUEST_DELAY)
            
            # Prepare headers
            headers = {
                "User-Agent": self.get_random_user_agent(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Connection": "keep-alive",
            }
            
            # Forward the request
            self.forward_request(url, headers)
            
        except Exception as e:
            logging.error(f"Error in do_GET: {str(e)}")
            self.send_error(500, str(e))

def run_server():
    """Run the proxy server with proper error handling."""
    try:
        # Initialize proxy pool on startup
        print("Initializing proxy pool...")
        update_proxy_pool()
        
        if not PROXY_POOL:
            print("Warning: No proxies loaded. Server will start but requests may fail.")
            logging.warning("No proxies available at startup")
        else:
            print(f"Loaded {len(PROXY_POOL)} proxies")
        
        # Start the periodic refresh timer
        start_proxy_refresh_timer()
        
        with socketserver.TCPServer(("", PORT), ProxyHandler) as httpd:
            print(f"Proxy server running on port {PORT}")
            print(f"Proxy pool will refresh every {PROXY_REFRESH_INTERVAL/60} minutes")
            logging.info(f"Server started on port {PORT}")
            httpd.serve_forever()
    except OSError as e:
        logging.error(f"Failed to start server: {e}")
        print(f"Error: Could not start server on port {PORT}. Port might be in use.")
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
        print("\nServer stopped by user")
    except Exception as e:
        logging.error(f"Unexpected server error: {e}")
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    run_server()