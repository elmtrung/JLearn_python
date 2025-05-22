from flask import Blueprint, request, jsonify
from app.services.db import get_user_collections

bp = Blueprint('collections', __name__)

@bp.route('/api/ml/get_collections', methods=['GET', 'POST'])
def get_collections():
    if request.method == 'GET':
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'Missing user_id parameter'}), 400
    elif request.method == 'POST':
        data = request.get_json()
        if not data or 'user_id' not in data:
            return jsonify({'error': 'Missing user_id in request body'}), 400
        user_id = data['user_id']

    collections = get_user_collections(user_id)
    if collections is None:
        return jsonify({'error': 'Failed to fetch collections'}), 500

    return jsonify({'user_id': user_id, 'collections': collections}) 