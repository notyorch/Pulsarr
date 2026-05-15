import os

# Configuration loaded from environment with sensible defaults
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
API_KEY = os.getenv('API_KEY')
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '8000'))
APP_ENV = os.getenv('APP_ENV', 'production')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
INCLUDE_RAW_JSON = os.getenv('INCLUDE_RAW_JSON', 'false').lower() in ('1','true','yes')
TELEGRAM_PARSE_MODE = os.getenv('TELEGRAM_PARSE_MODE') or None

# Gunicorn settings (optional)
GUNICORN_WORKERS = int(os.getenv('GUNICORN_WORKERS', '3'))
