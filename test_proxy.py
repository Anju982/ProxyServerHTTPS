#!/usr/bin/env python3
"""
Simple test script to verify the proxy server is working.
Usage: python test_proxy.py
"""

import urllib.request
import urllib.error
import time

def test_proxy_server():
    """Test the proxy server by making a request through it."""
    
    # Test URL - using a simple HTTP service
    test_url = "http://httpbin.org/ip"
    proxy_server = "http://localhost:8080"
    
    try:
        print("Testing proxy server...")
        print(f"Proxy server: {proxy_server}")
        print(f"Test URL: {test_url}")
        
        # Make request through our proxy server
        # The URL should be passed as the path to our proxy server
        proxy_url = f"{proxy_server}/{test_url}"
        
        print(f"Making request to: {proxy_url}")
        print("This may take a moment as the server tries different proxies...")
        
        start_time = time.time()
        
        with urllib.request.urlopen(proxy_url, timeout=60) as response:
            content = response.read().decode('utf-8')
            end_time = time.time()
            
            print(f"Response status: {response.status}")
            print(f"Response time: {end_time - start_time:.2f} seconds")
            print(f"Response content: {content}")
            print("✅ Proxy server test successful!")
            
    except urllib.error.HTTPError as e:
        error_content = ""
        try:
            error_content = e.read().decode('utf-8') if e.fp else 'No content'
        except Exception:
            error_content = 'Could not read error content'
            
        print(f"❌ HTTP Error: {e.code} - {e.reason}")
        print(f"Error details: {error_content[:200]}...")
        
        if e.code == 403:
            print("\n💡 This might be due to:")
            print("- Free proxies being blocked by the target server")
            print("- Proxies not working properly")
            print("- Need to wait for proxy validation to complete")
            
    except urllib.error.URLError as e:
        print(f"❌ URL Error: {e.reason}")
        print("\n💡 Make sure the proxy server is running on port 8080")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_direct_connection():
    """Test direct connection to verify the target URL works."""
    test_url = "http://httpbin.org/ip"
    
    try:
        print("\nTesting direct connection (without proxy)...")
        with urllib.request.urlopen(test_url, timeout=10) as response:
            content = response.read().decode('utf-8')
            print(f"✅ Direct connection successful: {content}")
    except Exception as e:
        print(f"❌ Direct connection failed: {e}")

if __name__ == "__main__":
    test_direct_connection()
    test_proxy_server()
