from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import asyncio
import logging

# Importa as configurações e os comandos dos outros ficheiros
from config import TOKEN, ADMIN_IDS
from database import load_video_db, load_user_ids, save_video_db, save_user_ids
from comandos_user import start, tutorial, ajuda, cupom, handle_user_message
from comandos_admin import (
    add_links, pendentes, addmanual, add, video, cancelar, enviar, 
    deletar_video, esgotado, bugado, handle_admin_message
)

# Configuração de logging para vermos os erros no output da Replit
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- CONFIGURAÇÃO DO BOT (MODO WEBHOOK) ---

async def setup_bot():
    """Configura e inicializa a aplicação do bot do Telegram."""
    application = Application.builder().token(TOKEN).build()

    # Carrega as bases de dados para a memória ao iniciar
    application.bot_data['video_db'] = load_video_db()
    application.bot_data['user_ids'] = load_user_ids()
    print(f"Bot a iniciar... {len(application.bot_data['user_ids'])} utilizadores carregados.")

    # --- Registo de Comandos ---
    admin_filter = filters.User(user_id=ADMIN_IDS)
    user_filter = ~admin_filter

    # Comandos para todos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("tutorial", tutorial))
    application.add_handler(CommandHandler("ajuda", ajuda))
    application.add_handler(CommandHandler("cupom", cupom))
    
    # Comandos de Admin
    application.add_handler(CommandHandler("enviar", enviar, admin_filter))
    for i in range(1, 7):
        application.add_handler(CommandHandler(f"add{i}", add_links, admin_filter))
    application.add_handler(CommandHandler("pendentes", pendentes, admin_filter))
    application.add_handler(CommandHandler("addmanual", addmanual, admin_filter))
    application.add_handler(CommandHandler("add", add, admin_filter))
    application.add_handler(CommandHandler("video", video, admin_filter))
    application.add_handler(CommandHandler("cancelar", cancelar, admin_filter))
    application.add_handler(CommandHandler("esgotado", esgotado, admin_filter))
    application.add_handler(CommandHandler("bugado", bugado, admin_filter))
    application.add_handler(CommandHandler("deletarvideo", deletar_video, admin_filter))

    # --- Processadores de Mensagens ---
    application.add_handler(MessageHandler(filters.PHOTO & admin_filter, enviar))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & admin_filter, handle_admin_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & user_filter, handle_user_message))
    
    return application

# --- CONFIGURAÇÃO DO SERVIDOR WEB (FLASK) ---

app = Flask(__name__)
bot_app = asyncio.run(setup_bot())

@app.route('/webhook', methods=['POST'])
async def webhook():
    """Processa as atualizações recebidas do Telegram."""
    try:
        update = Update.de_json(request.get_json(force=True), bot_app.bot)
        await bot_app.process_update(update)
        return jsonify(status='ok'), 200
    except Exception as e:
        logger.error(f"Erro no webhook: {e}")
        return jsonify(status='error', error=str(e)), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint para o UptimeRobot manter o bot 'acordado'."""
    return jsonify(status='ok'), 200

@app.route('/')
def index():
    """Página inicial que confirma que o bot está a funcionar."""
    return "Olá! O servidor do bot está a funcionar. Configure o webhook para /webhook.", 200

# Esta parte não é necessária para a Replit, mas é uma boa prática
if __name__ == '__main__':
    # O Gunicorn irá iniciar a aplicação, não precisamos de app.run()
    pass

