#!/usr/bin/env python3
"""
Simple mock dispatch server for testing CRM integration.
"""

import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs


class MockDispatchHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests to /api/workorders"""
        if self.path == "/api/workorders":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)

            try:
                # Parse JSON data
                work_order_data = json.loads(post_data.decode("utf-8"))

                # Validate required fields
                required_fields = ["customerName", "description", "technicianIds"]
                missing_fields = [
                    field for field in required_fields if field not in work_order_data
                ]

                if missing_fields:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    response = {
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": f"Missing required fields: {', '.join(missing_fields)}",
                            "details": [
                                {"field": field, "reason": "required"}
                                for field in missing_fields
                            ],
                        }
                    }
                    self.wfile.write(json.dumps(response).encode("utf-8"))
                    return

                # Generate mock response
                order_no = f"MOCK-{len(str(work_order_data))}"
                response_data = {
                    "id": f"workorder_{len(str(work_order_data))}",
                    "orderNo": order_no,
                    "customerName": work_order_data["customerName"],
                    "description": work_order_data["description"],
                    "status": "PENDING",
                    "createdAt": "2026-04-10T17:50:00Z",
                }

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode("utf-8"))

                print(f"✅ Created mock work order: {order_no}")
                print(f"   Customer: {work_order_data['customerName']}")
                print(f"   Description: {work_order_data['description']}")

            except json.JSONDecodeError:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                response = {
                    "error": {"code": "INVALID_JSON", "message": "Invalid JSON"}
                }
                self.wfile.write(json.dumps(response).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                response = {"error": {"code": "INTERNAL_ERROR", "message": str(e)}}
                self.wfile.write(json.dumps(response).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        """Handle health check"""
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy"}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3005))
    server = HTTPServer(("localhost", port), MockDispatchHandler)
    print(f"🚀 Mock dispatch server running on http://localhost:{port}")
    print(
        "This server simulates the IT dispatch system API for testing CRM integration."
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        server.server_close()
