from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import TOKEN, ADMIN_IDS
from database import load_video_db, load_user_ids

# Importa as funções de comando dos outros ficheiros
from comandos_user import (
    start,
    tutorial,
    ajuda,
    cupom,
    handle_user_message # Handler para utilizadores normais
)
from comandos_admin import (
    add_links,
    pendentes,
    addmanual,
    add,
    video,
    cancelar,
    enviar,
    esgotado,
    bugado,
    handle_admin_message # Handler para administradores
)

def main() -> None:
    """Função principal que configura e inicia o bot."""
    application = Application.builder().token(TOKEN).build()
    
    # Carrega as bases de dados para a memória ao iniciar
    application.bot_data['link_queue'] = []
    application.bot_data['video_db'] = load_video_db()
    application.bot_data['user_ids'] = load_user_ids()
    
    print(f"Bot a iniciar... {len(application.bot_data['user_ids'])} utilizadores carregados da base de dados.")

    # --- Registo de Comandos ---
    # Comandos para todos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("tutorial", tutorial))
    application.add_handler(CommandHandler("ajuda", ajuda))
    application.add_handler(CommandHandler("cupom", cupom))
    
    # Comandos de Admin
    for i in range(1, 7):
        application.add_handler(CommandHandler(f"add{i}", add_links, filters.User(user_id=ADMIN_IDS)))
    application.add_handler(CommandHandler("pendentes", pendentes, filters.User(user_id=ADMIN_IDS)))
    application.add_handler(CommandHandler("addmanual", addmanual, filters.User(user_id=ADMIN_IDS)))
    application.add_handler(CommandHandler("add", add, filters.User(user_id=ADMIN_IDS)))
    application.add_handler(CommandHandler("video", video, filters.User(user_id=ADMIN_IDS)))
    application.add_handler(CommandHandler("cancelar", cancelar, filters.User(user_id=ADMIN_IDS)))
    application.add_handler(CommandHandler("enviar", enviar, filters.User(user_id=ADMIN_IDS)))
    application.add_handler(CommandHandler("esgotado", esgotado, filters.User(user_id=ADMIN_IDS)))
    application.add_handler(CommandHandler("bugado", bugado, filters.User(user_id=ADMIN_IDS)))

    # --- CORREÇÃO: Processadores de Mensagens de Texto Separados ---
    # Filtro para mensagens de administradores que não são comandos
    admin_filter = filters.User(user_id=ADMIN_IDS)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & admin_filter, handle_admin_message))
    
    # Filtro para mensagens de utilizadores normais que não são comandos
    user_filter = ~filters.User(user_id=ADMIN_IDS)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & user_filter, handle_user_message))

    # Inicia o bot
    print("Bot com todas as funcionalidades implementadas iniciado!")
    application.run_polling()


if __name__ == '__main__':
    main()

