"""
Serverless prediction endpoint for Vercel (Python).
- Expects a serialized scikit-learn pipeline saved as joblib: model_rf_pipeline.joblib
- Receives JSON with numeric features and returns { label, probability }.

This file uses Starlette (lightweight ASGI) to avoid heavy frameworks.
Vercel detects the handler as `app`.
"""
from __future__ import annotations

import json
import math
import os
from typing import Any, Dict

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

try:
    from joblib import load as joblib_load
except Exception:  # pragma: no cover
    joblib_load = None

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'model_rf_pipeline.joblib')

# Features expected by the trained model (must match training data)
EXPECTED_FEATURES = [
    'step',
    'amount',
    'oldbalanceOrg',
    'newbalanceOrig',
    'oldbalanceDest',
    'newbalanceDest',
    'errorBalanceOrig',
    'errorBalanceDest',
    'type_CASH_OUT',
    'type_DEBIT',
    'type_PAYMENT',
    'type_TRANSFER',
]

_model = None

def _load_model():
    global _model
    if _model is not None:
        return _model
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            'Model file not found at api/model_rf_pipeline.joblib. Export your trained Random Forest pipeline and commit it.'
        )
    if joblib_load is None:
        raise RuntimeError('joblib is required to load the model but was not found.')
    _model = joblib_load(MODEL_PATH)
    return _model

async def predict(request: Request) -> Response:
    try:
        payload: Dict[str, Any] = await request.json()
    except Exception as e:
        return JSONResponse({'error': f'Invalid JSON: {str(e)}'}, status_code=400)

    # Extract features with defaults
    features = []
    try:
        for key in EXPECTED_FEATURES:
            v = float(payload.get(key, 0))
            if math.isnan(v) or math.isinf(v):
                v = 0.0
            features.append(v)
    except Exception as e:
        return JSONResponse({'error': f'Features must be numeric: {str(e)}'}, status_code=400)

    # Shape to (1, n_features)
    row = [features]

    try:
        model = _load_model()
        # scikit models expose predict_proba; for GBM binary class 1 prob
        if hasattr(model, 'predict_proba'):
            proba = float(model.predict_proba(row)[0][1])
        else:
            # Fallback: decision_function/logit -> convert to probability-ish
            raw = float(model.decision_function(row)[0])
            proba = 1 / (1 + math.exp(-raw))
        label = 'Fraud' if proba >= 0.5 else 'Legit'
        return JSONResponse({'label': label, 'probability': proba})
    except FileNotFoundError as e:
        return JSONResponse({'error': str(e)}, status_code=500)
    except Exception as e:
        return JSONResponse({'error': f'Prediction failed: {str(e)}'}, status_code=500)

# For Vercel deployment, we need to handle both the /api/predict route and direct function calls
routes = [Route('/predict', predict, methods=['POST']), Route('/api/predict', predict, methods=['POST'])]
app = Starlette(routes=routes)

# Export the handler function for Vercel
handler = app
