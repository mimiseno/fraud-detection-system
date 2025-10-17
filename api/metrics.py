import json
import os


def handler(request):
    # Handle CORS
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Content-Type': 'application/json'
    }
    
    if request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    try:
        # Get the directory of this file
        api_dir = os.path.dirname(__file__)
        precomp_path = os.path.join(api_dir, 'metrics_precomputed.json')
        
        # Try to load precomputed metrics
        if os.path.exists(precomp_path):
            with open(precomp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(data)
            }
        else:
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({'error': 'Metrics file not found'})
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }