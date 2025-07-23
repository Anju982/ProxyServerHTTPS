#!/usr/bin/env python3
"""
Test script for the quick proxy server (port 8081).
"""

import urllib.request
import urllib.error
import time

def test_quick_proxy_server():
    """Test the quick proxy server."""
    
    # Use a URL that works well with proxies
    test_url = "http://icanhazip.com"
    proxy_server = "http://localhost:8081"
    
    try:
        print("Testing quick proxy server...")
        print(f"Proxy server: {proxy_server}")
        print(f"Test URL: {test_url}")
        
        proxy_url = f"{proxy_server}/{test_url}"
        print(f"Making request to: {proxy_url}")
        
        start_time = time.time()
        
        with urllib.request.urlopen(proxy_url, timeout=30) as response:
            content = response.read().decode('utf-8')
            end_time = time.time()
            
            print(f"Response status: {response.status}")
            print(f"Response time: {end_time - start_time:.2f} seconds")
            print(f"Proxy IP: {content.strip()}")
            print("✅ Quick proxy server test successful!")
            
        # Test direct connection for comparison
        print("\nTesting direct connection for comparison...")
        start_time = time.time()
        with urllib.request.urlopen(test_url, timeout=10) as response:
            content = response.read().decode('utf-8')
            end_time = time.time()
            print(f"Direct IP: {content.strip()}")
            print(f"Direct response time: {end_time - start_time:.2f} seconds")
            
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error: {e.code} - {e.reason}")
        try:
            error_content = e.read().decode('utf-8') if e.fp else 'No content'
            print(f"Error details: {error_content[:200]}...")
        except Exception:
            print("Could not read error details")
            
    except urllib.error.URLError as e:
        print(f"❌ URL Error: {e.reason}")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_quick_proxy_server()
