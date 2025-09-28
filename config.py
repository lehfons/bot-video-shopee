import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do ficheiro .env
# Isto permite que as suas senhas fiquem seguras no servidor
load_dotenv()

# --- LÊ AS CONFIGURAÇÕES SECRETAS DO AMBIENTE ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
SHOPEE_APP_ID = os.getenv("SHOPEE_APP_ID")
SHOPEE_SECRET = os.getenv("SHOPEE_SECRET")

# --- CONFIGURAÇÕES NÃO SECRETAS ---
ADMIN_IDS = [1145078886] 

# Nomes dos ficheiros que servirão como a nossa base de dados
VIDEO_DB_FILE = 'video_database.json'
USER_DB_FILE = 'user_ids.json'

