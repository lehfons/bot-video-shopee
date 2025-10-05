import os
from dotenv import load_dotenv

# Carrega as variáveis do ficheiro .env (para testes locais)
load_dotenv()

# --- Chaves e Tokens ---
# O código agora lê as variáveis do ambiente do servidor de hospedagem
# Se a variável não for encontrada, ele usa None como padrão.
TOKEN = os.getenv("TELEGRAM_TOKEN")
SHOPEE_APP_ID = os.getenv("SHOPEE_APP_ID")
SHOPEE_SECRET = os.getenv("SHOPEE_SECRET")

# --- IDs de Administrador ---
# Converte a string de IDs de admin (separados por vírgula) para uma lista de inteiros
admin_ids_str = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(admin_id.strip()) for admin_id in admin_ids_str.split(',') if admin_id.strip()]

# --- Nomes dos Ficheiros de Base de Dados ---
# É importante que estes ficheiros sejam guardados num local persistente
VIDEO_DB_FILE = 'video_database.json'
USER_DB_FILE = 'user_ids.json'

