#!/usr/bin/env python3
"""
Test with different target URLs to see which ones work better with proxies.
"""

import urllib.request
import urllib.error
import time

def test_url_direct(url):
    """Test URL with direct connection."""
    try:
        print(f"\n🔗 Testing direct connection to: {url}")
        start_time = time.time()
        with urllib.request.urlopen(url, timeout=10) as response:
            end_time = time.time()
            content = response.read().decode('utf-8')[:100]
            print(f"✅ Direct: {response.status} ({end_time - start_time:.2f}s) - {content}...")
            return True
    except Exception as e:
        print(f"❌ Direct failed: {e}")
        return False

def test_url_via_proxy(url, proxy_port=8081):
    """Test URL via proxy server."""
    try:
        print(f"🔄 Testing via proxy: {url}")
        proxy_url = f"http://localhost:{proxy_port}/{url}"
        start_time = time.time()
        with urllib.request.urlopen(proxy_url, timeout=15) as response:
            end_time = time.time()
            content = response.read().decode('utf-8')[:100]
            print(f"✅ Proxy: {response.status} ({end_time - start_time:.2f}s) - {content}...")
            return True
    except Exception as e:
        print(f"❌ Proxy failed: {e}")
        return False

def main():
    test_urls = [
        "http://httpbin.org/ip",
        "http://httpbin.org/headers", 
        "http://example.com",
        "http://icanhazip.com",
        "http://ipinfo.io/ip"
    ]
    
    print("Testing various URLs with direct connection and proxy...")
    
    for url in test_urls:
        print(f"\n{'='*50}")
        print(f"Testing: {url}")
        
        # Test direct first
        direct_works = test_url_direct(url)
        
        # Test via proxy
        proxy_works = test_url_via_proxy(url)
        
        if direct_works and proxy_works:
            print("🎉 Both direct and proxy work!")
        elif direct_works and not proxy_works:
            print("⚠️ Only direct connection works")
        elif not direct_works and proxy_works:
            print("🤔 Only proxy works (unusual)")
        else:
            print("💥 Neither direct nor proxy works")

if __name__ == "__main__":
    main()
