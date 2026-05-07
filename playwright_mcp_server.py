#!/usr/bin/env python3
"""
Playwright MCP Server for Multi-Agent Research

This server provides MCP (Model Context Protocol) endpoints for browser automation.
It allows AI agents to control the browser, interact with the UI, and capture results.

Usage:
    python playwright_mcp_server.py

Endpoints:
    - /health: Health check
    - /screenshot: Capture screenshot
    - /navigate: Navigate to URL
    - /click: Click element
    - /type: Type text into element
    - /research: Run complete research workflow
    - /extract: Extract data from page
"""

import json
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, Optional
import threading

# Import the browser automation class
from tests.test_playwright import MultiAgentResearchBrowser


class PlaywrightMCPServer:
    """MCP Server for Playwright browser automation."""

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.browser = None
        self.server = None
        self.server_thread = None

    def start_browser(self, url: str = "http://127.0.0.1:7862"):
        """Start the browser instance."""
        if self.browser is None:
            self.browser = MultiAgentResearchBrowser(base_url=url)
            self.browser.start(headless=False)
            print(f"✓ Browser started at {url}")
        return self.browser

    def stop_browser(self):
        """Stop the browser instance."""
        if self.browser:
            self.browser.close()
            self.browser = None
            print("✓ Browser stopped")

    def handle_request(self, method: str, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests."""
        try:
            if method == "GET" and path == "/health":
                return {"status": "ok", "browser": "running" if self.browser else "stopped"}

            elif method == "POST" and path == "/start":
                url = params.get("url", "http://127.0.0.1:7862")
                self.start_browser(url)
                return {"status": "success", "message": f"Browser started at {url}"}

            elif method == "POST" and path == "/stop":
                self.stop_browser()
                return {"status": "success", "message": "Browser stopped"}

            elif method == "POST" and path == "/screenshot":
                if not self.browser:
                    return {"status": "error", "message": "Browser not started"}

                path = params.get("path", "screenshot.png")
                self.browser.take_screenshot(path)
                return {"status": "success", "path": path}

            elif method == "POST" and path == "/navigate":
                if not self.browser:
                    return {"status": "error", "message": "Browser not started"}

                url = params.get("url")
                if url:
                    self.browser.page.goto(url)
                    return {"status": "success", "url": url}
                return {"status": "error", "message": "URL required"}

            elif method == "POST" and path == "/click":
                if not self.browser:
                    return {"status": "error", "message": "Browser not started"}

                selector = params.get("selector")
                if selector:
                    self.browser.page.click(selector)
                    return {"status": "success", "selector": selector}
                return {"status": "error", "message": "Selector required"}

            elif method == "POST" and path == "/type":
                if not self.browser:
                    return {"status": "error", "message": "Browser not started"}

                selector = params.get("selector")
                text = params.get("text")

                if selector and text:
                    self.browser.page.fill(selector, text)
                    return {"status": "success", "selector": selector, "text": text}
                return {"status": "error", "message": "Selector and text required"}

            elif method == "POST" and path == "/research":
                if not self.browser:
                    return {"status": "error", "message": "Browser not started"}

                company = params.get("company")
                lang = params.get("lang", "EN")

                if company:
                    result = self.browser.run_research(company, lang)
                    return {
                        "status": "success",
                        "result": result
                    }
                return {"status": "error", "message": "Company name required"}

            elif method == "POST" and path == "/extract":
                if not self.browser:
                    return {"status": "error", "message": "Browser not started"}

                selector = params.get("selector")
                if selector:
                    content = self.browser.page.locator(selector).inner_text()
                    return {"status": "success", "content": content}
                return {"status": "error", "message": "Selector required"}

            elif method == "POST" and path == "/wait":
                if not self.browser:
                    return {"status": "error", "message": "Browser not started"}

                timeout = params.get("timeout", 5000)
                self.browser.page.wait_for_timeout(timeout)
                return {"status": "success", "timeout": timeout}

            elif method == "POST" and path == "/evaluate":
                if not self.browser:
                    return {"status": "error", "message": "Browser not started"}

                js = params.get("javascript")
                if js:
                    result = self.browser.page.evaluate(js)
                    return {"status": "success", "result": result}
                return {"status": "error", "message": "JavaScript required"}

            else:
                return {"status": "error", "message": f"Unknown endpoint: {path}"}

        except Exception as e:
            return {"status": "error", "message": str(e)}


class MCPRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for MCP server."""

    server_instance: PlaywrightMCPServer = None

    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path
        params = dict(parse_qs(parsed.query))

        # Flatten single-value params
        params = {k: v[0] if len(v) == 1 else v for k, v in params.items()}

        result = self.server_instance.handle_request("GET", path, params)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())

    def do_POST(self):
        """Handle POST requests."""
        parsed = urlparse(self.path)
        path = parsed.path

        # Read body
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode() if content_length > 0 else "{}"

        try:
            params = json.loads(body) if body else {}
        except json.JSONDecodeError:
            params = {}

        result = self.server_instance.handle_request("POST", path, params)

        self.send_response(200 if result["status"] == "success" else 400)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def run_server(host: str = "localhost", port: int = 8765):
    """Run the MCP server."""
    server_instance = PlaywrightMCPServer(host, port)
    MCPRequestHandler.server_instance = server_instance

    httpd = HTTPServer((host, port), MCPRequestHandler)

    print(f"\n{'='*60}")
    print(f"🎭 Playwright MCP Server")
    print(f"{'='*60}")
    print(f"Server running at http://{host}:{port}")
    print(f"\nAvailable endpoints:")
    print(f"  GET  /health              - Health check")
    print(f"  POST /start               - Start browser")
    print(f"  POST /stop                - Stop browser")
    print(f"  POST /screenshot          - Capture screenshot")
    print(f"  POST /navigate            - Navigate to URL")
    print(f"  POST /click               - Click element")
    print(f"  POST /type                - Type text")
    print(f"  POST /research            - Run research workflow")
    print(f"  POST /extract             - Extract page content")
    print(f"  POST /wait                - Wait for timeout")
    print(f"  POST /evaluate            - Execute JavaScript")
    print(f"\nPress Ctrl+C to stop\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        server_instance.stop_browser()
        httpd.shutdown()
        print("✓ Server stopped")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Playwright MCP Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8765, help="Port to listen on")

    args = parser.parse_args()
    run_server(args.host, args.port)
