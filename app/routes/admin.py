from flask import Blueprint, jsonify
from app.services.db import get_admin_metrics

bp = Blueprint('admin', __name__)

@bp.route('/api/ml/admin/metrics', methods=['GET'])
def get_metrics():
    metrics = get_admin_metrics()
    if metrics is None:
        return jsonify({'error': 'Failed to fetch admin metrics'}), 500
    
    print(f"Admin metrics: {metrics}")
    return jsonify(metrics) 