"""
Simple metrics endpoint for Vercel serverless functions.
"""
import json
import os
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Get the directory of this file
            api_dir = os.path.dirname(__file__)
            precomp_path = os.path.join(api_dir, 'metrics_precomputed.json')
            
            # Try to load precomputed metrics
            if os.path.exists(precomp_path):
                with open(precomp_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Set response headers
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                # Send response
                self.wfile.write(json.dumps(data).encode('utf-8'))
            else:
                # Return error if no metrics file found
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                error_data = {'error': 'Metrics file not found'}
                self.wfile.write(json.dumps(error_data).encode('utf-8'))
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_data = {'error': str(e)}
            self.wfile.write(json.dumps(error_data).encode('utf-8'))