from flask import Flask, request, jsonify
from asgiref.sync import async_to_sync  # Correct the import
import speech_recognition as sr
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
import os
import tempfile
import google.generativeai as genai
from googletrans import Translator  # Add this import

app = Flask(__name__)

genai.configure(api_key="AIzaSyDdIVT2V5A4L79oiyzsaRKPbsBJTEErlq4")
model = genai.GenerativeModel('gemini-2.0-flash')

def _load_and_convert_audio(audio_file_path):

    try:
        print("Đang đọc và chuyển đổi audio bằng Pydub...")
        audio = AudioSegment.from_file(audio_file_path)
    except CouldntDecodeError:
        print(f"Lỗi: Pydub không thể giải mã file '{audio_file_path}'. Định dạng có thể không được hỗ trợ.")
        return None
    except FileNotFoundError:
        print("Lỗi: Không tìm thấy FFmpeg. Vui lòng cài đặt FFmpeg và đảm bảo nó nằm trong PATH.")
        return None

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_f:
        temp_wav_path = temp_f.name
        print(f"Đang xuất sang file WAV tạm thời: {temp_wav_path}")
        audio.export(temp_wav_path, format="wav")
        return temp_wav_path

def _transcribe_audio(wav_file_path):
    recognizer = sr.Recognizer()
    print("Đang mở file WAV để nhận dạng...")
    try:
        with sr.AudioFile(wav_file_path) as source:
            audio_data = recognizer.record(source)
        print("Đang gửi dữ liệu đến Google Speech Recognition...")
        text = recognizer.recognize_google(audio_data, language="ja-JP")
        print("Nhận dạng thành công!")
        return text
    except sr.UnknownValueError:
        print("Google Speech Recognition không thể hiểu được nội dung âm thanh.")
        return None
    except sr.RequestError as e:
        print(f"Không thể kết nối hoặc yêu cầu kết quả từ Google Speech Recognition; {e}")
        return None

def analyze_japanese_text(text):
    prompt = f"""Hãy phân tích đoạn văn bản tiếng Nhật sau đây để tìm lỗi dùng từ không chính xác vì đây là một đoạn transcript ion được trích từ một audio đoạn có thể có lỗi khi nhận diện giọng nói và sau đó hãy phân tích ngữ pháp và đưa ra đề xuất sửa lỗi.
    Đoạn văn bản:
    {text}

    Phân tích và đề xuất sửa lỗi (nếu có):"""

    response = model.generate_content(prompt)
    return response.text

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']

    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.filename)[1]) as temp_audio_file:
        audio_file.save(temp_audio_file.name)
        audio_file_path = temp_audio_file.name

    print(f"File audio tạm thời đã lưu tại: {audio_file_path}")

    temp_wav_path = None
    try:
        temp_wav_path = _load_and_convert_audio(audio_file_path)
        if not temp_wav_path:
            return jsonify({'error': 'Failed to convert audio to WAV'}), 500

        transcription = _transcribe_audio(temp_wav_path)
        if not transcription:
            return jsonify({'error': 'Failed to transcribe audio'}), 500

        analysis_result = analyze_japanese_text(transcription)

        return jsonify({'transcription': transcription, 'analysis': analysis_result})

    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")
        return jsonify({'error': str(e)}), 500

    finally:
        if temp_wav_path and os.path.exists(temp_wav_path):
            os.remove(temp_wav_path)
        if os.path.exists(audio_file_path):
            os.remove(audio_file_path)
        print(f"Đã xóa file tạm: {temp_wav_path} và {audio_file_path}")

async def translate_japanese_to_vietnamese(text):
    translator = Translator()
    result = await translator.translate(text, src='ja', dest='vi')
    return result.text

@app.route('/translate', methods=['POST'])
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

if __name__ == '__main__':
    app.run(debug=True)
