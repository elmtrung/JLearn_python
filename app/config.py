import os

# ZaloPay config
ZALOPAY_CONFIG = {
    "appid": 553,
    "key1": "9phuAOYhan4urywHTh0ndEXiV3pKHr5Q",
    "key2": "Iyz2habzyr7AG8SgvoBCbKwKi3UzlLi3",
    "endpoint": "https://sandbox.zalopay.com.vn/v001/tpe/createorder",
    "status_endpoint": "https://sandbox.zalopay.com.vn/v001/tpe/getstatusbyapptransid"
}

# Database config
SQL_SERVER_DRIVER = os.environ.get('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
SQL_SERVER_HOST = os.environ.get('DB_HOST', '34.44.254.240,1433')
SQL_SERVER_DATABASE = os.environ.get('DB_NAME', 'JLearnDb')
SQL_SERVER_USER = os.environ.get('DB_USER', 'sa')
SQL_SERVER_PASSWORD = os.environ.get('DB_PASSWORD', 'Quangvinh16#')
SQL_SERVER_TRUST_SERVER_CERT = os.environ.get('DB_TRUST_SERVER_CERT', 'Yes')

# Gemini AI config
GEMINI_API_KEY = "AIzaSyDdIVT2V5A4L79oiyzsaRKPbsBJTEErlq4"

# CORS config
CORS_CONFIG = {
    "origins": ["http://localhost:3000"],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"],
    "supports_credentials": True
}

# Database connection string
SQL_SERVER_CONNECTION_STRING = f"Driver={{{SQL_SERVER_DRIVER}}};Server={SQL_SERVER_HOST};Database={SQL_SERVER_DATABASE};UID={SQL_SERVER_USER};PWD={SQL_SERVER_PASSWORD};TrustServerCertificate={SQL_SERVER_TRUST_SERVER_CERT};" 