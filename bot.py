import asyncio
from flask import Flask, request, Response
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Importa as configurações e os handlers dos outros ficheiros
from config import TOKEN, ADMIN_IDS
from database import load_video_db, load_user_ids
from comandos_user import start, tutorial, ajuda, cupom, handle_user_message
from comandos_admin import (
    add_links, pendentes, addmanual, add, video, cancelar, 
    enviar, deletar_video, esgotado, bugado, handle_admin_message
)

# Configuração do logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Configuração do Bot do Telegram ---
async def setup_bot():
    """Configura a aplicação do bot e retorna a instância."""
    application = Application.builder().token(TOKEN).build()

    # Carrega as bases de dados
    application.bot_data['link_queue'] = []
    application.bot_data['video_db'] = load_video_db()
    application.bot_data['user_ids'] = load_user_ids()
    logger.info(f"{len(application.bot_data['user_ids'])} utilizadores carregados da base de dados.")

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
    application.add_handler(CommandHandler("deletarvideo", deletar_video, admin_filter))
    application.add_handler(CommandHandler("esgotado", esgotado, admin_filter))
    application.add_handler(CommandHandler("bugado", bugado, admin_filter))

    # --- Processadores de Mensagens ---
    application.add_handler(MessageHandler(filters.PHOTO & admin_filter, enviar))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & admin_filter, handle_admin_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & user_filter, handle_user_message))
    
    return application

# --- Configuração da Aplicação Web (Flask) ---
app = Flask(__name__)
bot_app = asyncio.run(setup_bot())

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint para o UptimeRobot manter o bot 'acordado'."""
    return Response("OK", status=200)

@app.route('/webhook', methods=['POST'])
async def webhook():
    """Endpoint que recebe as atualizações do Telegram."""
    update_data = request.get_json()
    update = Update.de_json(update_data, bot_app.bot)
    await bot_app.process_update(update)
    return Response("OK", status=200)

# --- Função Principal ---
# A execução da aplicação é gerida pelo Gunicorn através do Procfile
# Esta parte não é executada diretamente na Koyeb, mas é útil para testes locais.
if __name__ == '__main__':
    # Para testes locais, você precisaria de configurar um túnel como o ngrok
    # e correr esta aplicação Flask. A forma mais fácil é testar com `run_polling`
    # antes de enviar para a Koyeb.
    logger.info("Aplicação web pronta para ser executada por um servidor WSGI (como Gunicorn).")

