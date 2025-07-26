#!/usr/bin/env python3
"""
Test HTTPS Proxy Server Functionality
This script tests both HTTP and HTTPS requests through the proxy server.

MIT License
Copyright (c) 2025 Anju982
Licensed under the MIT License. See LICENSE file for details.
"""

import urllib.request
import urllib.error
import time
import json

def test_https_proxy():
    """Test HTTPS requests through the proxy server"""
    
    # Test URLs - mix of HTTP and HTTPS
    test_cases = [
        {
            "name": "HTTP Request",
            "url": "http://localhost:8080/http://httpbin.org/ip",
            "description": "Simple HTTP request through proxy"
        },
        {
            "name": "HTTPS Request - HTTPBin",
            "url": "http://localhost:8080/https://httpbin.org/ip",
            "description": "HTTPS request to get IP through proxy"
        },
        {
            "name": "HTTPS Request - Example.com",
            "url": "http://localhost:8080/https://www.example.com",
            "description": "HTTPS request to example.com"
        },
        {
            "name": "HTTPS Request - JSONPlaceholder",
            "url": "http://localhost:8080/https://jsonplaceholder.typicode.com/posts/1",
            "description": "HTTPS API request"
        },
        {
            "name": "Auto HTTPS - Google",
            "url": "http://localhost:8080/google.com",
            "description": "Auto-detects HTTPS for google.com"
        }
    ]
    
    print("🧪 Testing HTTPS Proxy Server")
    print("=" * 60)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['name']}")
        print(f"   URL: {test['url']}")
        print(f"   Description: {test['description']}")
        print("   ", end="")
        
        try:
            start_time = time.time()
            
            # Create request with proper headers
            request = urllib.request.Request(
                test['url'],
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
            )
            
            with urllib.request.urlopen(request, timeout=20) as response:
                content = response.read()
                end_time = time.time()
                
                # Try to decode content
                try:
                    text_content = content.decode('utf-8')
                    
                    # Try to parse as JSON for pretty output
                    try:
                        json_data = json.loads(text_content)
                        content_preview = json.dumps(json_data, indent=2)[:200]
                    except json.JSONDecodeError:
                        content_preview = text_content[:200]
                        
                except UnicodeDecodeError:
                    content_preview = f"Binary content ({len(content)} bytes)"
                
                print(f"✅ SUCCESS")
                print(f"     Status: {response.status}")
                print(f"     Time: {end_time - start_time:.2f}s")
                print(f"     Content-Type: {response.getheader('content-type', 'unknown')}")
                print(f"     Size: {len(content)} bytes")
                print(f"     Preview: {content_preview[:100]}...")
                
        except urllib.error.HTTPError as e:
            print(f"❌ HTTP ERROR: {e.code} - {e.reason}")
            try:
                error_content = e.read().decode('utf-8')[:100]
                print(f"     Error details: {error_content}...")
            except:
                print(f"     Could not read error details")
                
        except urllib.error.URLError as e:
            print(f"❌ URL ERROR: {e.reason}")
            print(f"     This might indicate the proxy server is not running")
            
        except Exception as e:
            print(f"❌ ERROR: {type(e).__name__}: {e}")
        
        # Small delay between tests
        time.sleep(1)

def test_https_vs_http():
    """Compare HTTP vs HTTPS requests"""
    
    print(f"\n" + "=" * 60)
    print("🔍 HTTP vs HTTPS Comparison")
    print("=" * 60)
    
    # Test same endpoint with both protocols
    endpoints = [
        ("httpbin.org/ip", "Get IP address"),
        ("httpbin.org/user-agent", "Get user agent"),
        ("httpbin.org/headers", "Get request headers")
    ]
    
    for endpoint, description in endpoints:
        print(f"\n📍 Testing: {endpoint} - {description}")
        
        # Test HTTP
        http_url = f"http://localhost:8080/http://{endpoint}"
        print(f"   HTTP:  ", end="")
        test_single_url(http_url)
        
        # Test HTTPS  
        https_url = f"http://localhost:8080/https://{endpoint}"
        print(f"   HTTPS: ", end="")
        test_single_url(https_url)

def test_single_url(url):
    """Test a single URL and print result"""
    try:
        start_time = time.time()
        
        with urllib.request.urlopen(url, timeout=15) as response:
            content = response.read()
            end_time = time.time()
            
            print(f"✅ {response.status} ({end_time - start_time:.2f}s, {len(content)} bytes)")
            
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP {e.code}")
    except urllib.error.URLError as e:
        print(f"❌ Connection Error")
    except Exception as e:
        print(f"❌ {type(e).__name__}")

def show_usage_guide():
    """Show how to use the HTTPS proxy server"""
    
    print(f"\n" + "=" * 60)
    print("📖 HTTPS Proxy Server Usage Guide")
    print("=" * 60)
    
    print(f"""
🌐 Server URL: http://localhost:8080

📝 Usage Formats:
   • HTTP requests:  http://localhost:8080/http://example.com
   • HTTPS requests: http://localhost:8080/https://example.com  
   • Auto-detect:    http://localhost:8080/example.com

✨ Features:
   • Supports both HTTP and HTTPS requests
   • Automatic proxy rotation with fallback to direct connection
   • Handles compressed responses (gzip)
   • Random user agent rotation
   • SSL certificate verification disabled for proxy compatibility

🧪 Test Commands:
   curl "http://localhost:8080/https://httpbin.org/ip"
   curl "http://localhost:8080/http://httpbin.org/user-agent"
   curl "http://localhost:8080/google.com"

📊 Monitor with Status Dashboard:
   python simple_status.py
   Then visit: http://localhost:8888
""")

if __name__ == "__main__":
    print("🚀 HTTPS Proxy Server Test Suite")
    print("Make sure your proxy server is running on port 8080!")
    print("Start it with: python https_proxy_server.py")
    
    input("\nPress Enter to start tests...")
    
    test_https_proxy()
    test_https_vs_http()
    show_usage_guide()
    
    print(f"\n✅ Testing complete!")
    print(f"💡 Tip: Use the status dashboard at http://localhost:8888 for interactive testing")
