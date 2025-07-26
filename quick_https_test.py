#!/usr/bin/env python3
"""
Quick HTTPS Proxy Test
Automated testing of HTTPS proxy functionality

MIT License
Copyright (c) 2025 Anju982
Licensed under the MIT License. See LICENSE file for details.
"""

import urllib.request
import urllib.error
import time

def test_url(url, description):
    """Test a single URL through the proxy"""
    proxy_url = f"http://localhost:8080/{url}"
    
    print(f"\n🧪 {description}")
    print(f"   URL: {proxy_url}")
    
    try:
        start_time = time.time()
        
        with urllib.request.urlopen(proxy_url, timeout=10) as response:
            duration = time.time() - start_time
            content = response.read()
            
            print(f"   ✅ SUCCESS")
            print(f"      Status: {response.status}")
            print(f"      Time: {duration:.2f}s")
            print(f"      Size: {len(content)} bytes")
            
            # Show preview of content
            preview = content.decode('utf-8', errors='ignore')[:100]
            print(f"      Preview: {preview}...")
            
            return True
            
    except Exception as e:
        duration = time.time() - start_time
        print(f"   ❌ FAILED")
        print(f"      Error: {str(e)}")
        print(f"      Time: {duration:.2f}s")
        
        return False

def main():
    """Run all tests"""
    print("🚀 Quick HTTPS Proxy Test Suite")
    print("=" * 50)
    
    tests = [
        ("https://httpbin.org/ip", "HTTPS IP Check"),
        ("https://www.example.com", "HTTPS Example.com"),
        ("https://jsonplaceholder.typicode.com/posts/1", "HTTPS JSON API"),
        ("http://httpbin.org/user-agent", "HTTP User Agent"),
        ("google.com", "Auto-HTTPS Detection"),
    ]
    
    passed = 0
    total = len(tests)
    
    for url, description in tests:
        if test_url(url, description):
            passed += 1
        time.sleep(1)  # Brief delay between tests
    
    print(f"\n📊 Test Results:")
    print(f"   Passed: {passed}/{total}")
    print(f"   Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("   🎉 All tests passed! HTTPS proxy is working perfectly!")
    elif passed > 0:
        print("   🔶 Some tests passed. Check failing tests above.")
    else:
        print("   ❌ All tests failed. Check if proxy server is running.")

if __name__ == "__main__":
    main()
