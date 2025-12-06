import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / '.env')

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
# SESSION_PATH should be like: session/telegram  (Telethon will append .session)
SESSION_PATH = os.getenv('SESSION_PATH')
if not SESSION_PATH:
    raise RuntimeError('SESSION_PATH not set in .env')

# base folder where downloads/thumbs will be stored
SAVE_BASE = os.getenv('SAVE_BASE', str(BASE_DIR / 'data'))