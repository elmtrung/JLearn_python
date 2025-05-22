import os
import tempfile
import speech_recognition as sr
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
import google.generativeai as genai
from app.config import GEMINI_API_KEY

# Configure Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

def load_and_convert_audio(audio_file_path):
    """Loads and converts audio file to WAV format."""
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

def transcribe_audio(wav_file_path):
    """Transcribes audio file to text using Google Speech Recognition."""
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

def analyze_japanese_text(text, additional_text):
    """Analyzes Japanese text using Gemini AI."""
    prompt = f"""
    với câu hỏi {additional_text}
    Hãy phân tích đoạn văn bản tiếng Nhật sau đây để tìm lỗi dùng từ không chính xác vì đây là một đoạn transcript ion được trích từ một audio đoạn có thể có lỗi khi nhận diện giọng nói và sau đó hãy phân tích ngữ pháp và đưa ra đề xuất sửa lỗi.
    Đoạn văn bản:
    {text}

    Phân tích và đề xuất sửa lỗi (nếu có):
    1. Phân tích lỗi dùng từ
    2. Phân tích ngữ pháp
    3. Đề xuất sửa lỗi và giải thích
    4. Kết luận

    Hãy trả về kết quả theo định dạng sau:
    [TRANSCRIPTION]
    {text}

    [PHÂN TÍCH LỖI DÙNG TỪ]
    - Liệt kê các lỗi dùng từ và giải thích

    [PHÂN TÍCH NGỮ PHÁP]
    - Phân tích cấu trúc ngữ pháp của câu

    [ĐỀ XUẤT SỬA LỖI]
    - Đưa ra các phiên bản sửa lỗi và giải thích

    [KẾT LUẬN]
    - Tóm tắt và đưa ra phiên bản chính xác nhất
    """

    response = model.generate_content(prompt)
    return response.text

def remove_asterisks(text):
    """Removes asterisks from text."""
    return text.replace('*', '') if text else text 