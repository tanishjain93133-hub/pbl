import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'smartpark-super-secret-key-pbl1-2026')
    
    # Environment detection
    IS_VERCEL = bool(os.getenv('VERCEL') or os.getenv('AWS_LAMBDA_FUNCTION_NAME'))
    
    # DB configuration
    # Default to sqlite if running on Vercel / serverless and no explicit remote MySQL host is provided
    default_db_type = 'sqlite' if (IS_VERCEL and (not os.getenv('MYSQL_HOST') or os.getenv('MYSQL_HOST') == 'localhost')) else 'mysql'
    DB_TYPE = os.getenv('DB_TYPE', default_db_type).lower()
    
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DB = os.getenv('MYSQL_DB', 'smart_parking')
    
    # SQLite file path - Vercel / AWS Lambda only permits writing to /tmp
    if IS_VERCEL:
        SQLITE_DB_PATH = '/tmp/smart_parking.db'
    else:
        SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'smart_parking.db')
    
    FLASK_ENV = os.getenv('FLASK_ENV', 'production' if IS_VERCEL else 'development')
    DEBUG = os.getenv('FLASK_DEBUG', '0' if IS_VERCEL else '1') == '1'

