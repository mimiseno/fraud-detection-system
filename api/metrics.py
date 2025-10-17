"""
Dynamic metrics endpoint for the dashboard.

Loads one or more serialized models (GBM primary, optional RF and DT) and a
small test set JSON, computes metrics, and returns the same shape used by the
frontend. Any missing model is skipped gracefully.

Files looked for in this folder:
- model_gbm_pipeline.joblib (required for GBM metrics)
- model_rf_pipeline.joblib (optional)
- model_dt_pipeline.joblib (optional)
- test_set_small.json (required)  -> list of {<feature>: value, "label": 0|1}

Response shape:
{
  "source": "dynamic",
  "count": <n>,
  "models": [{"name": str, "metrics": {accuracy, precision, recall, f1, roc_auc}}]
}
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterable, List, Tuple

from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from joblib import load as joblib_load
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

API_DIR = os.path.dirname(__file__)
TEST_SET_PATH = os.path.join(API_DIR, 'test_set_small.json')
PRECOMP_PATH = os.path.join(API_DIR, 'metrics_precomputed.json')

EXPECTED_FEATURES = [
    'amount', 'oldbalanceOrg', 'newbalanceOrg', 'oldbalanceDest', 'newbalanceDest', 'isCashOut', 'isTransfer'
]

MODEL_FILES = [
    ('Random Forest', os.path.join(API_DIR, 'model_rf_pipeline.joblib')),
    ('GBM', os.path.join(API_DIR, 'model_gbm_pipeline.joblib')),
    ('Decision Tree', os.path.join(API_DIR, 'model_dt_pipeline.joblib')),
]

def _load_test_set() -> Tuple[List[List[float]], List[int]]:
    if not os.path.exists(TEST_SET_PATH):
        raise FileNotFoundError('Missing api/test_set_small.json. Export a small holdout set from your notebook.')
    with open(TEST_SET_PATH, 'r', encoding='utf-8') as f:
        rows = json.load(f)
    X: List[List[float]] = []
    y: List[int] = []
    for row in rows:
        X.append([float(row.get(k, 0)) for k in EXPECTED_FEATURES])
        y.append(int(row.get('label', 0)))
    return X, y

def _metrics(y_true: Iterable[int], y_pred: Iterable[int], y_prob: Iterable[float]) -> Dict[str, float]:
    return {
        'accuracy': float(accuracy_score(y_true, y_pred)),
        'precision': float(precision_score(y_true, y_pred, zero_division=0)),
        'recall': float(recall_score(y_true, y_pred, zero_division=0)),
        'f1': float(f1_score(y_true, y_pred, zero_division=0)),
        'roc_auc': float(roc_auc_score(y_true, y_prob)) if len(set(y_true)) > 1 else 0.0,
    }

async def metrics_endpoint(_) -> Response:
    # If a precomputed metrics file exists (exported from the notebook), return that.
    if os.path.exists(PRECOMP_PATH):
        try:
            with open(PRECOMP_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Ensure the expected envelope
            data['source'] = data.get('source', 'precomputed')
            return JSONResponse(data)
        except Exception as e:
            # Fall through to dynamic computation if reading fails
            pass

    try:
        X, y_true = _load_test_set()
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)

    out = {'source': 'dynamic', 'count': len(X), 'models': []}

    for name, path in MODEL_FILES:
        if not os.path.exists(path):
            continue
        try:
            model = joblib_load(path)
            if hasattr(model, 'predict_proba'):
                y_prob = model.predict_proba(X)[:, 1].tolist()
            else:
                # Fallback: logits -> probability via logistic
                import math
                logits = model.decision_function(X).tolist()
                y_prob = [1 / (1 + math.exp(-z)) for z in logits]
            y_pred = [1 if p >= 0.5 else 0 for p in y_prob]
            out['models'].append({'name': name, 'metrics': _metrics(y_true, y_pred, y_prob)})
        except Exception as e:  # continue on error for a model
            out['models'].append({'name': name, 'error': f'failed: {e}'})

    if not out['models']:
        return JSONResponse({'error': 'No models found. Add joblib files under api/.'}, status_code=500)

    return JSONResponse(out)

# Vercel handler function
def handler(request):
    """Vercel serverless function handler"""
    import asyncio
    return asyncio.run(metrics_endpoint(request))
