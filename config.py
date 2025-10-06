import os
import re

# --- LEITURA DAS VARIÁVEIS DE AMBIENTE (SECRETS) ---
# Esta é a forma segura de ler as suas senhas na Replit

TOKEN = os.getenv("TELEGRAM_TOKEN")
SHOPEE_APP_ID = os.getenv("SHOPEE_APP_ID")
SHOPEE_SECRET = os.getenv("SHOPEE_SECRET")

# Lê a variável de admins e converte-a numa lista de números inteiros
admin_ids_str = os.getenv("ADMIN_IDS", "")
try:
    # Remove espaços e divide a string pela vírgula, convertendo cada parte para um número
    ADMIN_IDS = [int(admin_id.strip()) for admin_id in admin_ids_str.split(',') if admin_id.strip()]
except ValueError:
    print("AVISO: A variável ADMIN_IDS contém um valor inválido. Apenas IDs numéricos são permitidos.")
    ADMIN_IDS = []

# Nomes dos ficheiros de base de dados
VIDEO_DB_FILE = 'video_database.json'
USER_DB_FILE = 'user_ids.json'

# --- VALIDAÇÃO DAS CONFIGURAÇÕES ---
# Verifica se as senhas essenciais foram carregadas corretamente

if not TOKEN:
    raise ValueError("ERRO CRÍTICO: O TELEGRAM_TOKEN não foi encontrado nos Secrets. O bot não pode iniciar.")
if not SHOPEE_APP_ID:
    print("AVISO: O SHOPEE_APP_ID não foi encontrado nos Secrets.")
if not SHOPEE_SECRET:
    print("AVISO: O SHOPEE_SECRET não foi encontrado nos Secrets.")
if not ADMIN_IDS:
    print("AVISO: A variável ADMIN_IDS está vazia ou inválida. Nenhum admin será reconhecido.")

