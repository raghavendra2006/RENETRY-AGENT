import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

db_env = os.environ.get('DATABASE_PATH')
if db_env:
    DATABASE_PATH = db_env if os.path.isabs(db_env) else os.path.join(BASE_DIR, db_env)
else:
    DATABASE_PATH = os.path.join(BASE_DIR, 'return_platform.db')

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 're_turn_platform_secret_key_2026_secure_hash')
    DATABASE_PATH = DATABASE_PATH
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    ALLOWED_RESUME_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt'}
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_PERMANENT = False
    
    # Server-Side AI Configuration
    AI_API_KEY = os.environ.get('AI_API_KEY', '').strip()
    AI_PROVIDER = os.environ.get('AI_PROVIDER', 'gemini').lower().strip()
    AI_MODEL = os.environ.get('AI_MODEL', 'gemini-flash-latest').strip()

    # Roadmap Progression Configuration
    ROADMAP_PASSING_SCORE = float(os.environ.get('ROADMAP_PASSING_SCORE', 70.0))
