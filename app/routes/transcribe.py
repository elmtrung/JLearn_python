from flask import Blueprint, request, jsonify
import os
import tempfile
import traceback
from app.services.audio import load_and_convert_audio, transcribe_audio, analyze_japanese_text, remove_asterisks

bp = Blueprint('transcribe', __name__)

@bp.route('/api/ml/transcribe', methods=['POST'])
def transcribe_audio_route():
    if 'audio' not in request.files:
        print("No audio file part in request.files")
        return jsonify({'error': 'No audio file provided. Make sure to use form-data with a file field named "audio".'}), 400

    audio_file = request.files['audio']
    if audio_file.filename == '':
        print("Audio file field is present but filename is empty")
        return jsonify({'error': 'Empty audio file provided (filename is empty).'}), 400

    additional_text = request.form.get('additional_text', '').strip()
    print(f"additional_text: {additional_text}")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.filename)[1]) as temp_audio_file:
            audio_file.save(temp_audio_file.name)
            audio_file_path = temp_audio_file.name

        print(f"File audio tạm thời đã lưu tại: {audio_file_path}")

        temp_wav_path = None
        try:
            temp_wav_path = load_and_convert_audio(audio_file_path)
            if not temp_wav_path:
                return jsonify({'error': 'Failed to convert audio to WAV'}), 500

            transcription = transcribe_audio(temp_wav_path)
            if not transcription:
                return jsonify({'error': 'Failed to transcribe audio'}), 500

            analysis_result = analyze_japanese_text(transcription, additional_text)
            cleaned_analysis_result = remove_asterisks(analysis_result)
            print("analysis_result:", cleaned_analysis_result)
            print("transcription:", transcription)
            return jsonify({
                'transcription': transcription,
                'additional_text': additional_text,
                'analysis_result': cleaned_analysis_result
            })

        except Exception as e:
            print(f"Đã xảy ra lỗi: {e}")
            traceback_str = traceback.format_exc()
            print(traceback_str)
            return jsonify({'error': str(e), 'traceback': traceback_str}), 500

        finally:
            if temp_wav_path and os.path.exists(temp_wav_path):
                os.remove(temp_wav_path)
            if os.path.exists(audio_file_path):
                os.remove(audio_file_path)
            print(f"Đã xóa file tạm: {temp_wav_path} và {audio_file_path}")

    except Exception as e:
        print(f"Error processing request: {e}")
        traceback_str = traceback.format_exc()
        print(traceback_str)
        return jsonify({'error': str(e), 'traceback': traceback_str}), 500 