#!/usr/bin/env python3
"""
Simple Proxy Server Status Dashboard (No External Dependencies)
A lightweight web-based status page using only built-in Python libraries.
Usage: python simple_status.py
Access: http://localhost:8888

MIT License
Copyright (c) 2025 Anju982
Licensed under the MIT License. See LICENSE file for details.
"""

import time
import json
import threading
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import socket
import subprocess
import os

class SimpleProxyMonitor:
    def __init__(self):
        self.proxy_url = "http://localhost:8080"
        self.test_endpoints = [
            {"name": "HTTP Test", "url": "http://httpbin.org/ip"},
            {"name": "HTTPS Test", "url": "https://httpbin.org/ip"},
            {"name": "Example.com", "url": "https://www.example.com"},
        ]
        self.status_history = []
        self.current_status = {
            "proxy_running": False,
            "last_check": None,
            "test_results": [],
            "uptime": None,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0
        }
        self.start_time = datetime.now()
        
    def check_proxy_status(self):
        """Check if proxy server is running"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('localhost', 8080))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def test_endpoint(self, endpoint):
        """Test endpoint through proxy"""
        proxy_url = f"{self.proxy_url}/{endpoint['url']}"
        
        try:
            start_time = time.time()
            request = urllib.request.Request(
                proxy_url,
                headers={'User-Agent': 'SimpleStatusMonitor/1.0'}
            )
            
            with urllib.request.urlopen(request, timeout=10) as response:
                end_time = time.time()
                response_time = end_time - start_time
                content_length = len(response.read())
                
                return {
                    "name": endpoint["name"],
                    "url": endpoint["url"],
                    "status": "success",
                    "status_code": response.status,
                    "response_time": round(response_time, 2),
                    "content_length": content_length,
                    "timestamp": datetime.now().isoformat()
                }
        except urllib.error.HTTPError as e:
            return {
                "name": endpoint["name"],
                "url": endpoint["url"],
                "status": "http_error",
                "status_code": e.code,
                "error": f"{e.code} - {e.reason}",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "name": endpoint["name"],
                "url": endpoint["url"],
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_simple_system_info(self):
        """Get basic system info using built-in tools"""
        try:
            # Check if proxy process is running
            proxy_running = False
            try:
                result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
                if 'app.py' in result.stdout:
                    proxy_running = True
            except Exception:
                pass
            
            # Get load average (Linux/Unix)
            load_avg = "N/A"
            try:
                with open('/proc/loadavg', 'r') as f:
                    load_avg = f.read().split()[0]
            except Exception:
                pass
            
            return {
                "proxy_process_detected": proxy_running,
                "load_average": load_avg,
                "timestamp": datetime.now().isoformat()
            }
        except Exception:
            return {"error": "Could not get system info"}
    
    def run_status_check(self):
        """Run complete status check"""
        print(f"🔍 Running status check at {datetime.now().strftime('%H:%M:%S')}")
        
        # Check proxy
        proxy_running = self.check_proxy_status()
        
        # Test endpoints
        test_results = []
        if proxy_running:
            for endpoint in self.test_endpoints:
                result = self.test_endpoint(endpoint)
                test_results.append(result)
                
                self.current_status["total_requests"] += 1
                if result["status"] == "success":
                    self.current_status["successful_requests"] += 1
                else:
                    self.current_status["failed_requests"] += 1
        
        # Calculate average response time
        successful_results = [r for r in test_results if "response_time" in r and r["response_time"]]
        avg_response_time = 0
        if successful_results:
            avg_response_time = sum(r["response_time"] for r in successful_results) / len(successful_results)
        
        # Update status
        self.current_status.update({
            "proxy_running": proxy_running,
            "last_check": datetime.now().isoformat(),
            "test_results": test_results,
            "uptime": str(datetime.now() - self.start_time).split('.')[0],
            "average_response_time": round(avg_response_time, 2)
        })
        
        # Update history
        self.status_history.append({
            "timestamp": datetime.now().isoformat(),
            "proxy_running": proxy_running,
            "successful_tests": len([r for r in test_results if r["status"] == "success"]),
            "total_tests": len(test_results)
        })
        
        if len(self.status_history) > 20:
            self.status_history = self.status_history[-20:]

class SimpleStatusHandler(BaseHTTPRequestHandler):
    def __init__(self, monitor, *args, **kwargs):
        self.monitor = monitor
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        if self.path == '/':
            self.serve_dashboard()
        elif self.path == '/api/status':
            self.serve_status_api()
        elif self.path == '/api/check':
            threading.Thread(target=self.monitor.run_status_check, daemon=True).start()
            self.send_json_response({"message": "Status check initiated"})
        elif self.path.startswith('/api/test-url?'):
            self.handle_url_test()
        else:
            self.send_error(404)
    
    def handle_url_test(self):
        """Handle custom URL testing"""
        try:
            # Parse URL from query string
            query_string = self.path.split('?', 1)[1]
            params = {}
            for param in query_string.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key] = urllib.parse.unquote(value)
            
            test_url = params.get('url', '')
            if not test_url:
                self.send_json_response({"error": "No URL provided"})
                return
            
            # Test the URL through proxy
            result = self.test_custom_url(test_url)
            self.send_json_response(result)
            
        except Exception as e:
            self.send_json_response({"error": str(e)})
    
    def test_custom_url(self, test_url):
        """Test a custom URL through the proxy"""
        proxy_url = f"http://localhost:8080/{test_url}"
        
        try:
            start_time = time.time()
            request = urllib.request.Request(
                proxy_url,
                headers={'User-Agent': 'CustomURLTester/1.0'}
            )
            
            with urllib.request.urlopen(request, timeout=15) as response:
                end_time = time.time()
                response_time = end_time - start_time
                content = response.read()
                content_text = content.decode('utf-8', errors='ignore')
                
                return {
                    "status": "success",
                    "test_url": test_url,
                    "proxy_url": proxy_url,
                    "status_code": response.status,
                    "response_time": round(response_time, 2),
                    "content_length": len(content),
                    "content_type": response.headers.get('content-type', 'unknown'),
                    "content_preview": content_text[:500] + "..." if len(content_text) > 500 else content_text,
                    "timestamp": datetime.now().isoformat()
                }
        except urllib.error.HTTPError as e:
            error_content = ""
            try:
                error_content = e.read().decode('utf-8', errors='ignore')[:300]
            except Exception:
                pass
                
            return {
                "status": "http_error",
                "test_url": test_url,
                "proxy_url": proxy_url,
                "status_code": e.code,
                "error": f"{e.code} - {e.reason}",
                "error_content": error_content,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "test_url": test_url,
                "proxy_url": proxy_url,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def serve_dashboard(self):
        html = self.get_simple_dashboard_html()
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def serve_status_api(self):
        status_data = {
            "current_status": self.monitor.current_status,
            "history": self.monitor.status_history,
            "system_info": self.monitor.get_simple_system_info()
        }
        self.send_json_response(status_data)
    
    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def get_simple_dashboard_html(self):
        return '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Proxy Server Status</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .header { background: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 8px; margin-bottom: 20px; }
        .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .status-online { color: #4CAF50; font-weight: bold; }
        .status-offline { color: #f44336; font-weight: bold; }
        .test-success { background: #e8f5e8; padding: 10px; margin: 5px 0; border-radius: 4px; border-left: 4px solid #4CAF50; }
        .test-error { background: #ffeaea; padding: 10px; margin: 5px 0; border-radius: 4px; border-left: 4px solid #f44336; }
        .btn { background: #4CAF50; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
        .btn:hover { background: #45a049; }
        .metric { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }
        .history { display: flex; gap: 2px; height: 50px; align-items: end; }
        .history-bar { width: 10px; background: #ddd; border-radius: 2px; }
        .history-success { background: #4CAF50; }
        .history-partial { background: #ff9800; }
        .history-failed { background: #f44336; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌐 Proxy Server Status Dashboard</h1>
        <p>Monitoring localhost:8080</p>
    </div>
    
    <div class="card">
        <h3>📊 Current Status</h3>
        <div class="metric">
            <span>Proxy Server:</span>
            <span id="proxy-status">Checking...</span>
        </div>
        <div class="metric">
            <span>Last Check:</span>
            <span id="last-check">Never</span>
        </div>
        <div class="metric">
            <span>Uptime:</span>
            <span id="uptime">--</span>
        </div>
    </div>
    
    <div class="card">
        <h3>📈 Statistics</h3>
        <div class="metric">
            <span>Total Requests:</span>
            <span id="total-requests">0</span>
        </div>
        <div class="metric">
            <span>Successful:</span>
            <span id="successful-requests">0</span>
        </div>
        <div class="metric">
            <span>Failed:</span>
            <span id="failed-requests">0</span>
        </div>
        <div class="metric">
            <span>Avg Response Time:</span>
            <span id="avg-response-time">0s</span>
        </div>
    </div>
    
    <div class="card">
        <h3>🌐 Custom URL Tester</h3>
        <p>Test any website through your proxy server:</p>
        <div style="margin: 15px 0;">
            <input type="url" id="custom-url" placeholder="https://example.com" style="width: 70%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
            <button class="btn" onclick="testCustomURL()" id="test-url-btn" style="margin-left: 10px;">🔍 Test URL</button>
        </div>
        <div id="custom-url-result" style="margin-top: 15px;">
            <p>Enter a URL and click "Test URL" to check its availability through your proxy.</p>
        </div>
    </div>
    
    <div class="card">
        <h3>🧪 Endpoint Tests</h3>
        <button class="btn" onclick="runCheck()" id="check-btn">🔍 Run Status Check</button>
        <div id="test-results" style="margin-top: 15px;">
            <p>Click "Run Status Check" to test endpoints...</p>
        </div>
    </div>
    
    <div class="card">
        <h3>📊 Status History</h3>
        <div class="history" id="history-chart">
            <p>No history data</p>
        </div>
    </div>

    <script>
        async function fetchStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                updateDashboard(data);
            } catch (error) {
                console.error('Error:', error);
            }
        }
        
        async function runCheck() {
            const btn = document.getElementById('check-btn');
            btn.textContent = '⏳ Running...';
            btn.disabled = true;
            
            try {
                await fetch('/api/check');
                setTimeout(() => {
                    fetchStatus();
                    btn.textContent = '🔍 Run Status Check';
                    btn.disabled = false;
                }, 2000);
            } catch (error) {
                btn.textContent = '🔍 Run Status Check';
                btn.disabled = false;
            }
        }
        
        async function testCustomURL() {
            const urlInput = document.getElementById('custom-url');
            const btn = document.getElementById('test-url-btn');
            const resultDiv = document.getElementById('custom-url-result');
            
            const testUrl = urlInput.value.trim();
            if (!testUrl) {
                resultDiv.innerHTML = '<div class="test-error">❌ Please enter a valid URL</div>';
                return;
            }
            
            // Add protocol if missing
            let finalUrl = testUrl;
            if (!testUrl.startsWith('http://') && !testUrl.startsWith('https://')) {
                finalUrl = 'https://' + testUrl;
            }
            
            btn.textContent = '⏳ Testing...';
            btn.disabled = true;
            
            resultDiv.innerHTML = `
                <div style="padding: 10px; background: #f0f8ff; border-left: 4px solid #2196F3; border-radius: 4px;">
                    ⏳ Testing URL: <strong>${finalUrl}</strong><br>
                    <small>This may take a few seconds...</small>
                </div>
            `;
            
            try {
                const response = await fetch(`/api/test-url?url=${encodeURIComponent(finalUrl)}`);
                const data = await response.json();
                
                if (data.error) {
                    resultDiv.innerHTML = `
                        <div class="test-error">
                            ❌ <strong>Error:</strong> ${data.error}
                        </div>
                    `;
                } else if (data.status === 'success') {
                    resultDiv.innerHTML = `
                        <div class="test-success">
                            ✅ <strong>Success!</strong><br>
                            <strong>URL:</strong> ${data.test_url}<br>
                            <strong>Status:</strong> ${data.status_code}<br>
                            <strong>Response Time:</strong> ${data.response_time}s<br>
                            <strong>Content Type:</strong> ${data.content_type}<br>
                            <strong>Content Length:</strong> ${data.content_length} bytes<br>
                            <details style="margin-top: 10px;">
                                <summary>Content Preview</summary>
                                <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; white-space: pre-wrap; font-size: 12px; max-height: 200px; overflow-y: auto;">${data.content_preview}</pre>
                            </details>
                        </div>
                    `;
                } else if (data.status === 'http_error') {
                    resultDiv.innerHTML = `
                        <div class="test-error">
                            ⚠️ <strong>HTTP Error:</strong><br>
                            <strong>URL:</strong> ${data.test_url}<br>
                            <strong>Status Code:</strong> ${data.status_code}<br>
                            <strong>Error:</strong> ${data.error}<br>
                            ${data.error_content ? `<details style="margin-top: 10px;">
                                <summary>Error Details</summary>
                                <pre style="background: #fff5f5; padding: 10px; border-radius: 4px; white-space: pre-wrap; font-size: 12px;">${data.error_content}</pre>
                            </details>` : ''}
                        </div>
                    `;
                } else {
                    resultDiv.innerHTML = `
                        <div class="test-error">
                            ❌ <strong>Connection Error:</strong><br>
                            <strong>URL:</strong> ${data.test_url}<br>
                            <strong>Error:</strong> ${data.error}<br>
                            <small>This could be due to proxy server issues, network problems, or the website blocking proxy requests.</small>
                        </div>
                    `;
                }
            } catch (error) {
                resultDiv.innerHTML = `
                    <div class="test-error">
                        ❌ <strong>Request Failed:</strong> ${error.message}
                    </div>
                `;
            }
            
            btn.textContent = '🔍 Test URL';
            btn.disabled = false;
        }
        
        // Allow Enter key to trigger URL test
        document.addEventListener('DOMContentLoaded', function() {
            const urlInput = document.getElementById('custom-url');
            urlInput.addEventListener('keypress', function(event) {
                if (event.key === 'Enter') {
                    testCustomURL();
                }
            });
        });
        
        function updateDashboard(data) {
            const { current_status, history } = data;
            
            // Update status
            const statusEl = document.getElementById('proxy-status');
            if (current_status.proxy_running) {
                statusEl.innerHTML = '<span class="status-online">● Online</span>';
            } else {
                statusEl.innerHTML = '<span class="status-offline">● Offline</span>';
            }
            
            document.getElementById('last-check').textContent = 
                current_status.last_check ? new Date(current_status.last_check).toLocaleString() : 'Never';
            document.getElementById('uptime').textContent = current_status.uptime || '--';
            
            // Update stats
            document.getElementById('total-requests').textContent = current_status.total_requests;
            document.getElementById('successful-requests').textContent = current_status.successful_requests;
            document.getElementById('failed-requests').textContent = current_status.failed_requests;
            document.getElementById('avg-response-time').textContent = current_status.average_response_time + 's';
            
            // Update test results
            const testsEl = document.getElementById('test-results');
            if (current_status.test_results && current_status.test_results.length > 0) {
                testsEl.innerHTML = current_status.test_results.map(test => {
                    const cssClass = test.status === 'success' ? 'test-success' : 'test-error';
                    const statusText = test.status === 'success' 
                        ? `✅ ${test.status_code} - ${test.response_time}s`
                        : `❌ ${test.error}`;
                    
                    return `
                        <div class="${cssClass}">
                            <strong>${test.name}</strong><br>
                            <small>${test.url}</small><br>
                            ${statusText}
                        </div>
                    `;
                }).join('');
            }
            
            // Update history
            const historyEl = document.getElementById('history-chart');
            if (history && history.length > 0) {
                historyEl.innerHTML = history.map(entry => {
                    const successRate = entry.total_tests > 0 ? entry.successful_tests / entry.total_tests : 0;
                    let barClass = 'history-failed';
                    if (successRate === 1) barClass = 'history-success';
                    else if (successRate > 0) barClass = 'history-partial';
                    
                    const height = Math.max(5, successRate * 40);
                    return `<div class="history-bar ${barClass}" style="height: ${height}px;" title="${new Date(entry.timestamp).toLocaleString()}"></div>`;
                }).join('');
            }
        }
        
        // Load initially and refresh every 30 seconds
        fetchStatus();
        setInterval(fetchStatus, 30000);
    </script>
</body>
</html>
        '''
    
    def log_message(self, format, *args):
        pass  # Suppress logs

def create_handler(monitor):
    def handler(*args, **kwargs):
        return SimpleStatusHandler(monitor, *args, **kwargs)
    return handler

def main():
    print("🚀 Starting Simple Proxy Status Dashboard...")
    
    monitor = SimpleProxyMonitor()
    monitor.run_status_check()
    
    handler = create_handler(monitor)
    httpd = HTTPServer(('localhost', 8888), handler)
    
    print("✅ Status dashboard running at: http://localhost:8888")
    print("📊 Monitoring proxy server at: http://localhost:8080")
    print("🔄 Auto-refresh every 30 seconds")
    print("⏹️  Press Ctrl+C to stop")
    
    # Background monitoring every 60 seconds
    def background_monitor():
        while True:
            time.sleep(60)
            monitor.run_status_check()
    
    threading.Thread(target=background_monitor, daemon=True).start()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹️  Shutting down...")
        httpd.shutdown()

if __name__ == "__main__":
    main()
