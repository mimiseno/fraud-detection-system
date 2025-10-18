import json
import os
import math

def handler(request):
    if request.method == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            "body": ""
        }
    
    if request.method != "POST":
        return {
            "statusCode": 405,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json"
            },
            "body": json.dumps({"error": "Method not allowed"})
        }
    
    try:
        if hasattr(request, "body"):
            body = request.body
        elif hasattr(request, "data"):
            body = request.data
        else:
            body = request.get_data()
            
        if isinstance(body, bytes):
            body = body.decode("utf-8")
            
        request_data = json.loads(body)
        
        api_dir = os.path.dirname(__file__)
        model_path = os.path.join(api_dir, "model_rf_pipeline.joblib")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError("Model file not found")
        
        from joblib import load as joblib_load
        model = joblib_load(model_path)
        
        features = [
            "amount", "oldbalanceOrg", "newbalanceOrg", "oldbalanceDest", 
            "newbalanceDest", "isCashOut", "isTransfer"
        ]
        
        row = []
        for feature in features:
            if feature in ["isCashOut", "isTransfer"]:
                if feature == "isCashOut":
                    row.append(float(request_data.get("type_CASH_OUT", 0)))
                else:
                    row.append(float(request_data.get("type_TRANSFER", 0)))
            else:
                row.append(float(request_data.get(feature, 0)))
        
        row_array = [row]
        
        if hasattr(model, "predict_proba"):
            proba = float(model.predict_proba(row_array)[0][1])
        else:
            raw = float(model.decision_function(row_array)[0])
            proba = 1 / (1 + math.exp(-raw))
        
        label = "Fraud" if proba >= 0.5 else "Legit"
        
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json"
            },
            "body": json.dumps({"label": label, "probability": proba})
        }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Content-Type": "application/json"
            },
            "body": json.dumps({"error": str(e)})
        }
