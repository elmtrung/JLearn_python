from flask import Blueprint, request, jsonify
from app.services.translation import translate_japanese_to_vietnamese
from asgiref.sync import async_to_sync

bp = Blueprint('translate', __name__)

@bp.route('/translate', methods=['POST'])
def translate_text():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400

    text = data['text']

    try:
        translated_text = async_to_sync(translate_japanese_to_vietnamese)(text)
        return jsonify({'original_text': text, 'translated_text': translated_text})
    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")
        return jsonify({'error': str(e)}), 500 