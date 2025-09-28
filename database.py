import json
import os
from config import VIDEO_DB_FILE, USER_DB_FILE

def load_video_db():
    """Carrega a base de dados de vídeos do ficheiro JSON."""
    if os.path.exists(VIDEO_DB_FILE):
        with open(VIDEO_DB_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {} # Retorna um dicionário vazio se o ficheiro estiver corrompido ou vazio
    return {}

def save_video_db(data):
    """Guarda a base de dados de vídeos no ficheiro JSON."""
    with open(VIDEO_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_user_ids():
    """Carrega o conjunto de IDs de utilizadores do ficheiro JSON."""
    if os.path.exists(USER_DB_FILE):
        with open(USER_DB_FILE, 'r', encoding='utf-8') as f:
            try:
                return set(json.load(f))
            except json.JSONDecodeError:
                return set()
    return set()

def save_user_ids(data):
    """Guarda o conjunto de IDs de utilizadores no ficheiro JSON."""
    with open(USER_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(data), f, indent=4)

