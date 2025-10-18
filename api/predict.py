from http.server import BaseHTTPRequestHandler
import json
import os
import math


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            api_dir = os.path.dirname(__file__)
            model_path = os.path.join(api_dir, 'model_rf_pipeline.joblib')
            
            if not os.path.exists(model_path):
                raise FileNotFoundError('Model file not found')
            
            from joblib import load as joblib_load
            model = joblib_load(model_path)
            
            features = [
                'amount', 'oldbalanceOrg', 'newbalanceOrg', 'oldbalanceDest', 
                'newbalanceDest', 'isCashOut', 'isTransfer'
            ]
            
            row = []
            for feature in features:
                if feature in ['isCashOut', 'isTransfer']:
                    if feature == 'isCashOut':
                        row.append(float(request_data.get('type_CASH_OUT', 0)))
                    else:
                        row.append(float(request_data.get('type_TRANSFER', 0)))
                else:
                    row.append(float(request_data.get(feature, 0)))
            
            row_array = [row]
            
            if hasattr(model, 'predict_proba'):
                proba = float(model.predict_proba(row_array)[0][1])
            else:
                raw = float(model.decision_function(row_array)[0])
                proba = 1 / (1 + math.exp(-raw))
            
            label = 'Fraud' if proba >= 0.5 else 'Legit'
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_data = {'label': label, 'probability': proba}
            self.wfile.write(json.dumps(response_data).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_data = {'error': str(e)}
            self.wfile.write(json.dumps(error_data).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()