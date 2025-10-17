import json
import os
import math

def handler(request, response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    
    if request.method == "OPTIONS":
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return ""
    
    if request.method != "POST":
        response.status_code = 405
        return {"error": "Method not allowed"}
    
    try:
        request_data = json.loads(request.body)
        
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
        
        return {"label": label, "probability": proba}
        
    except Exception as e:
        response.status_code = 500
        return {"error": str(e)}
