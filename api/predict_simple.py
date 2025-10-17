"""
Simple prediction endpoint for Vercel serverless functions.
"""
import json
import os
import math
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            # Load model
            api_dir = os.path.dirname(__file__)
            model_path = os.path.join(api_dir, 'model_rf_pipeline.joblib')
            
            if not os.path.exists(model_path):
                raise FileNotFoundError("Model file not found")
            
            # Import joblib here to avoid startup issues
            from joblib import load as joblib_load
            model = joblib_load(model_path)
            
            # Prepare features in expected order
            features = [
                'amount', 'oldbalanceOrg', 'newbalanceOrg', 'oldbalanceDest', 
                'newbalanceDest', 'isCashOut', 'isTransfer'
            ]
            
            # Extract values, handling missing keys gracefully
            row = []
            for feature in features:
                if feature in ['isCashOut', 'isTransfer']:
                    # These are derived from transaction type
                    if feature == 'isCashOut':
                        row.append(float(request_data.get('type_CASH_OUT', 0)))
                    else:  # isTransfer
                        row.append(float(request_data.get('type_TRANSFER', 0)))
                else:
                    row.append(float(request_data.get(feature, 0)))
            
            # Make prediction
            row_array = [row]  # Wrap in array for sklearn
            
            if hasattr(model, 'predict_proba'):
                proba = float(model.predict_proba(row_array)[0][1])
            else:
                # Fallback for models without predict_proba
                raw = float(model.decision_function(row_array)[0])
                proba = 1 / (1 + math.exp(-raw))
            
            label = 'Fraud' if proba >= 0.5 else 'Legit'
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_data = {'label': label, 'probability': proba}
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_data = {'error': str(e)}
            self.wfile.write(json.dumps(error_data).encode('utf-8'))

    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()