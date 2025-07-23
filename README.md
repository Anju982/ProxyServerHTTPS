# Proxy Server for Web Scraping

This is a Python-based proxy server that automatically fetches and rotates free HTTP proxies from ProxyScrape API for web scraping purposes.

## Features

- **Automatic Proxy Fetching**: Fetches up to 500 free proxies from ProxyScrape API
- **Auto-Refresh**: Refreshes proxy list every 30 minutes
- **User-Agent Rotation**: Randomly rotates user agents for each request
- **Request Delay**: Configurable delay between requests (default: 1 second)
- **Comprehensive Logging**: Logs all activities to `proxy.log`
- **Error Handling**: Robust error handling with fallback mechanisms

## Configuration

You can modify these settings in `app.py`:

```python
PORT = 8080                    # Server port
REQUEST_DELAY = 1              # Delay between requests (seconds)
TIMEOUT = 30                   # Request timeout (seconds)
PROXY_REFRESH_INTERVAL = 1800  # Proxy refresh interval (30 minutes)
```

## Usage

### Starting the Server

```bash
python app.py
```

The server will:
1. Fetch initial proxy list from ProxyScrape API
2. Start listening on port 8080
3. Begin automatic proxy refresh every 30 minutes

### Making Requests Through the Proxy

To use the proxy server, make HTTP requests to:
```
http://localhost:8080/TARGET_URL
```

**Example:**
```bash
# Direct request
curl "http://localhost:8080/http://httpbin.org/ip"

# Or using Python
import urllib.request
response = urllib.request.urlopen("http://localhost:8080/http://example.com")
```

### Testing the Server

Use the included test script:
```bash
python test_proxy.py
```

## API Source

Proxies are fetched from:
```
https://api.proxyscrape.com/v4/free-proxy-list/get?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all&skip=0&limit=500
```

## Logging

All activities are logged to `proxy.log` with timestamps, including:
- Server startup/shutdown
- Proxy fetching and refresh operations
- Request forwarding success/failures
- Error details

## Important Notes

⚠️ **Free Proxy Limitations:**
- Free proxies may be unreliable or slow
- Some proxies may not work at all
- Response times can vary significantly
- Consider using paid proxy services for production use

⚠️ **Legal Considerations:**
- Ensure you comply with target website's robots.txt and terms of service
- Respect rate limits and don't overload servers
- Use responsibly and ethically

## Error Handling

The server includes comprehensive error handling for:
- Network timeouts
- Invalid URLs
- Proxy connection failures
- HTTP errors
- Server startup issues

## Dependencies

- Python 3.6+
- Standard library modules only (no external dependencies)

## License

This project is for educational and development purposes. Use responsibly and in accordance with applicable laws and website terms of service.
