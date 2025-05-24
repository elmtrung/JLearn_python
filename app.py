from flask import Flask, request, jsonify
from flask_cors import CORS
from asgiref.sync import async_to_sync  # Correct the import
import speech_recognition as sr
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
import os
import tempfile
import google.generativeai as genai
from googletrans import Translator  # Add this import
import uuid, json, hmac, hashlib, urllib.request, urllib.parse
from datetime import datetime
from time import time
import pyodbc  
import traceback  

# ZaloPay config
ZALOPAY_CONFIG = {
    "appid": 553,
    "key1": "9phuAOYhan4urywHTh0ndEXiV3pKHr5Q",
    "key2": "Iyz2habzyr7AG8SgvoBCbKwKi3UzlLi3",
    "endpoint": "https://sandbox.zalopay.com.vn/v001/tpe/createorder",
    "status_endpoint": "https://sandbox.zalopay.com.vn/v001/tpe/getstatusbyapptransid"
}


SQL_SERVER_DRIVER = os.environ.get('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
SQL_SERVER_HOST = os.environ.get('DB_HOST', 'sqlserver')
SQL_SERVER_DATABASE = os.environ.get('DB_NAME', 'JLearnDb')
SQL_SERVER_USER = os.environ.get('DB_USER', 'sa')
SQL_SERVER_PASSWORD = os.environ.get('DB_PASSWORD', 'Quangvinh16#')
SQL_SERVER_TRUST_SERVER_CERT = os.environ.get('DB_TRUST_SERVER_CERT', 'Yes')

app = Flask(__name__)
# CORS(app)

CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000", "https://japstudy.id.vn"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

genai.configure(api_key="AIzaSyDdIVT2V5A4L79oiyzsaRKPbsBJTEErlq4")
model = genai.GenerativeModel('gemini-2.0-flash')

# Temporary store for pending orders. In production, use a persistent store like Redis or a database.
pending_orders = {}

# SQL_SERVER_CONNECTION_STRING = f"Driver={{{SQL_SERVER_DRIVER}}};Server={SQL_SERVER_HOST};Database={SQL_SERVER_DATABASE};UID={SQL_SERVER_USER};PWD={SQL_SERVER_PASSWORD};TrustServerCertificate={SQL_SERVER_TRUST_SERVER_CERT};"
SQL_SERVER_CONNECTION_STRING = (
    f"Driver={{{SQL_SERVER_DRIVER}}};"
    f"Server={SQL_SERVER_HOST};"
    f"Database={SQL_SERVER_DATABASE};"
    f"UID={SQL_SERVER_USER};"
    f"PWD={SQL_SERVER_PASSWORD};"
    f"TrustServerCertificate={SQL_SERVER_TRUST_SERVER_CERT};"
    f"Encrypt=False;"
)

def get_db_connection():
    """Establishes a connection to the SQL Server database using the provided connection string."""
    try:
        conn = pyodbc.connect(SQL_SERVER_CONNECTION_STRING)
        print("Connection String: ", SQL_SERVER_CONNECTION_STRING)
        return conn
    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        print(f"Database connection error: {sqlstate} - Connection string: {SQL_SERVER_CONNECTION_STRING}")
        return None

def add_transaction_to_db(user_id, collection_id, amount_paid, apptransid):
    """Adds a transaction record to the database."""
    conn = get_db_connection()
    if not conn:
        print(f"Failed to connect to database for apptransid {apptransid}. Transaction not recorded.")
        return False

    cursor = conn.cursor()
    transaction_id = str(uuid.uuid4())
    
    # Corrected table name from "Transaction" to "Transactions"
    sql = """
    INSERT INTO Transactions (TransactionID, UserID, CollectionID, AmountPaid, TransactionDate)
    VALUES (?, ?, ?, ?, GETDATE())
    """
    try:
        cursor.execute(sql, transaction_id, user_id, collection_id, float(amount_paid))  # Ensure amount is float
        conn.commit()
        print(f"Transaction {transaction_id} for apptransid {apptransid} recorded successfully.")
        return True
    except pyodbc.Error as e:
        print(f"Database error while inserting transaction for apptransid {apptransid}: {e}")
        conn.rollback()
        return False
    finally:
        if conn:
            cursor.close()
            conn.close()

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

def analyze_japanese_text(text, additional_text):
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

@app.route('/api/ml/transcribe', methods=['POST'])
def transcribe_audio():
  
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
            temp_wav_path = _load_and_convert_audio(audio_file_path)
            if not temp_wav_path:
                return jsonify({'error': 'Failed to convert audio to WAV'}), 500

            transcription = _transcribe_audio(temp_wav_path)
            if not transcription:
                return jsonify({'error': 'Failed to transcribe audio'}), 500

            analysis_result = analyze_japanese_text(transcription, additional_text)
            def remove_asterisks(text):
                return text.replace('*', '') if text else text

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

def create_zalopay_order(amount=50000, description="ZaloPay Integration Demo"):
    order = {
        "appid": ZALOPAY_CONFIG["appid"],
        "apptransid": "{:%y%m%d}_{}".format(datetime.today(), uuid.uuid4()),
        "appuser": "demo",
        "apptime": int(round(time() * 1000)),
        "embeddata": json.dumps({ 
            "merchantinfo": "embeddata123"
        }),
        "item": json.dumps([
            { "itemid": "knb", "itemname": "khoahoc", "itemprice": 198400, "itemquantity": 1 }
        ]),
        "amount": amount,
        "description": description,
        "bankcode": "zalopayapp"
    }
    data = "{}|{}|{}|{}|{}|{}|{}".format(
        order["appid"], order["apptransid"], order["appuser"], 
        order["amount"], order["apptime"], order["embeddata"], order["item"]
    )
    order["mac"] = hmac.new(ZALOPAY_CONFIG['key1'].encode(), data.encode(), hashlib.sha256).hexdigest()
    return order

def send_zalopay_order(order):
    response = urllib.request.urlopen(
        url=ZALOPAY_CONFIG["endpoint"], 
        data=urllib.parse.urlencode(order).encode()
    )
    result = json.loads(response.read())
    return result

def get_zalopay_order_status(apptransid):
    params = {
        "appid": ZALOPAY_CONFIG["appid"],
        "apptransid": apptransid
    }
    data = "{}|{}|{}".format(params["appid"], params["apptransid"], ZALOPAY_CONFIG["key1"])
    params["mac"] = hmac.new(ZALOPAY_CONFIG['key1'].encode(), data.encode(), hashlib.sha256).hexdigest()
    response = urllib.request.urlopen(
        url=ZALOPAY_CONFIG["status_endpoint"], 
        data=urllib.parse.urlencode(params).encode()
    )
    result = json.loads(response.read())
    return result

@app.route('/api/ml/create_order', methods=['POST'])
def create_order():
    req = request.get_json() or {}
    amount = req.get('amount', 50000)
    description = req.get('description', "ZaloPay Integration Demo")

    user_id = req.get('user_id')
    collection_id = req.get('collection_id')

    if not user_id or not collection_id:
        return jsonify({'error': 'user_id and collection_id are required in the request body'}), 400

    try:
        order_payload = create_zalopay_order(amount, description)
        apptransid = order_payload["apptransid"]

       
        pending_orders[apptransid] = {
            "user_id": user_id,
            "collection_id": collection_id,
            "amount": amount  
        }
        
        result = send_zalopay_order(order_payload)

        return jsonify({
            "order_payload": order_payload, 
            "zalopay_response": result
        })
    except Exception as e:
        print(f"Error creating ZaloPay order: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ml/order_status', methods=['GET'])
def order_status():
    apptransid = request.args.get('apptransid')
    if not apptransid:
        return jsonify({'error': 'Missing apptransid parameter'}), 400
    
    try:
        zalopay_status_result = get_zalopay_order_status(apptransid)
        

        if zalopay_status_result.get("returncode") == 1:
            order_details = pending_orders.get(apptransid)
            if order_details:
                print(f"Payment successful for apptransid: {apptransid}. Attempting to record transaction.")
                amount_paid = order_details["amount"]

                db_success = add_transaction_to_db(
                    user_id=order_details["user_id"],
                    collection_id=order_details["collection_id"],
                    amount_paid=amount_paid,
                    apptransid=apptransid
                )
                if db_success:
                    pending_orders.pop(apptransid, None) 
                    print(f"Transaction for {apptransid} processed and removed from pending orders.")
                else:
                    print(f"Failed to record transaction for {apptransid} in DB. It remains in pending_orders.")
                    zalopay_status_result["database_update_status"] = "failed"
            else:
    
                print(f"Order details not found in pending_orders for successful apptransid: {apptransid}. Transaction may have already been processed or an error occurred.")
                zalopay_status_result["internal_status"] = "Order details not found for successful payment."
        else:

            print(f"Payment not successful for apptransid: {apptransid}. ZaloPay Status: {zalopay_status_result.get('returnmessage')}")
      

        return jsonify(zalopay_status_result)
    except Exception as e:
        print(f"Error getting order status or processing transaction for apptransid {apptransid}: {e}")
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/ml/get_collections', methods=['GET'])
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

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Failed to connect to the database'}), 500

    try:
        cursor = conn.cursor()
        sql = "SELECT CollectionID FROM Transactions WHERE UserID = ?"
        cursor.execute(sql, user_id)
        collections = [row.CollectionID for row in cursor.fetchall()]
        return jsonify({'user_id': user_id, 'collections': collections})
        print(f"Fetched collections for user_id {user_id}: {collections}")
    
    except pyodbc.Error as e:
        print(f"Database error while fetching collections for user_id {user_id}: {e}")
        return jsonify({'error': 'Database query failed'}), 500
    finally:
        if conn:
            cursor.close()
            conn.close()

@app.route('/api/ml/admin/metrics', methods=['GET'])
def get_admin_metrics():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Failed to connect to the database'}), 500

    try:
        cursor = conn.cursor()
        
        # Lấy tổng số user và số user mới trong 30 ngày gần nhất
        cursor.execute("""
            SELECT 
                COUNT(*) as total_users,
                SUM(CASE WHEN CreatedAt >= DATEADD(day, -30, GETDATE()) THEN 1 ELSE 0 END) as new_users
            FROM Users
        """)
        user_row = cursor.fetchone()
        total_users = user_row.total_users
        new_users = user_row.new_users

        # Lấy tổng doanh thu
        cursor.execute("SELECT ISNULL(SUM(CAST(AmountPaid as decimal(18,2))), 0) as total_revenue FROM Transactions")
        total_revenue = float(cursor.fetchone().total_revenue)

        # Lấy tăng trưởng user 6 tháng gần nhất
        cursor.execute("""
            SELECT 
                FORMAT(CreatedAt, 'MMM') as month,
                COUNT(*) as count
            FROM Users
            WHERE CreatedAt >= DATEADD(month, -6, GETDATE())
            GROUP BY FORMAT(CreatedAt, 'MMM'), DATEPART(month, CreatedAt)
            ORDER BY DATEPART(month, MIN(CreatedAt))
        """)
        user_growth = [{'month': row.month, 'count': row.count} for row in cursor.fetchall()]

        metrics = {
            'totalUsers': total_users,
            'newUsers': new_users,
            'totalRevenue': total_revenue,
            'userGrowth': user_growth
        }
        return jsonify(metrics)
    except pyodbc.Error as e:
        print(f"Database error while fetching metrics: {e}")
        return jsonify({'error': 'Database query failed'}), 500
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
