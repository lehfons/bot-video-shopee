from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
import re # Importa a biblioteca de expressões regulares
from config import ADMIN_IDS
from database import save_user_ids
from api_shopee import resolve_short_link

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Regista o ID do utilizador, envia uma mensagem de boas-vindas e o menu apropriado."""
    user_id = update.effective_user.id
    context.user_data.clear()
    
    user_ids = context.bot_data['user_ids']
    if user_id not in user_ids:
        user_ids.add(user_id)
        save_user_ids(user_ids)
        print(f"Novo utilizador registado permanentemente: {user_id}. Total: {len(user_ids)}")

    if user_id in ADMIN_IDS:
        mensagem_start = (
            "Olá, veja como utilizar os comandos\n\n"
            "🔹 **/add1 a /add6**: Carrega produtos da fila.\n"
            "🔹 **/pendentes**: Mostra a quantidade de produtos na fila.\n"
            "🔹 **/addmanual**: Adiciona produtos manualmente.\n"
            "🔹 **/video <link>**: Envia o vídeo para os utilizadores do último lote.\n"
            "🔹 **/esgotado <link>**: Notifica o utilizador que o produto está esgotado.\n"
            "🔹 **/bugado <link>**: Notifica o utilizador que o produto está bugado.\n"
            "🔹 **Responder a uma mensagem de suporte encaminhada** para falar com o utilizador."
        )
        admin_keyboard_layout = [
            ['/add1', '/add2', '/add3'],
            ['/add4', '/add5', '/add6'],
            ['/pendentes', '/addmanual', '/enviar'],
            ['/esgotado', '/bugado', '/cancelar'],
            ['/video']
        ]
        keyboard = ReplyKeyboardMarkup(admin_keyboard_layout, resize_keyboard=True)
    else:
        mensagem_start = "Olá! Bem-vindo(a) ao Bot de Adicionar Produtos na Shopee Vídeos 🛍️\n\nSelecione uma opção no menu abaixo:"
        user_keyboard_layout = [['/tutorial', '/ajuda', '/cupom']]
        keyboard = ReplyKeyboardMarkup(user_keyboard_layout, resize_keyboard=True)
    await update.message.reply_text(mensagem_start, reply_markup=keyboard)

async def tutorial(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envia uma mensagem de tutorial atualizada."""
    mensagem_tutorial = (
        "✨ Como enviar o link correto ✨\n\n"
        "Para que eu possa processar o seu pedido, preciso do link completo do produto.\n\n"
        "1. Abra o produto no site ou no aplicativo da Shopee.\n"
        "2. Use a opção 'Compartilhar' (ícone de seta).\n"
        "3. Escolha a opção 'Copiar link'.\n\n"
        "Envie apenas links de produtos."
    )
    await update.message.reply_text(mensagem_tutorial)

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Informa o utilizador como obter suporte."""
    await update.message.reply_text(
        "Precisa de ajuda? Basta enviar a sua pergunta ou o seu problema aqui no chat.\n\n"
        "A sua mensagem será encaminhada para um administrador, que responderá assim que possível através do bot."
    )

async def cupom(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envia uma mensagem com links para cupons e para o grupo."""
    link_cupons_do_dia = "https://s.shopee.com.br/3VTwUqcjjN"
    link_grupo_cupons = "https://t.me/cupom_desconto"

    mensagem = (
        "Olá! 👋\n\n"
        "Quer economizar ainda mais? Aqui estão os melhores cupons do dia!\n\n"
        f"🎟️ **Acesse os Cupons Diários:** \n{link_cupons_do_dia}\n\n"
        f"💬 **Entre no nosso Grupo de Cupons:** \n"
        "Não perca nenhuma oferta! Participe do nosso grupo exclusivo para receber os melhores cupons em primeira mão.\n"
        f"{link_grupo_cupons}"
    )
    await update.message.reply_text(mensagem, disable_web_page_preview=True)

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processa todas as mensagens de texto de utilizadores normais, distinguindo submissões de links de pedidos de suporte."""
    user = update.effective_user
    user_id = user.id
    message_text = update.message.text
    
    # Regista o ID do utilizador na base de dados se for a primeira vez
    user_ids = context.bot_data['user_ids']
    if user_id not in user_ids:
        user_ids.add(user_id)
        save_user_ids(user_ids)
        print(f"Novo utilizador registado (via mensagem): {user_id}. Total: {len(user_ids)}")

    # Encontra o primeiro URL na mensagem que se pareça com um link da Shopee
    match = re.search(r'https?://[^\s]*(shopee|shp\.ee)[^\s]*', message_text, re.IGNORECASE)
    
    is_support_request = True # Assume que é um pedido de suporte por defeito
    shopee_link = None
    
    if match:
        shopee_link = match.group(0)
        # Verifica se a mensagem inteira é apenas o link (ignorando espaços em branco)
        if message_text.strip() == shopee_link:
            is_support_request = False

    if not is_support_request:
        # --- FLUXO DE SUBMISSÃO DE PRODUTO ---
        processing_message = await update.message.reply_text("A verificar o seu link, por favor aguarde...")
        
        resolved_link = resolve_short_link(shopee_link) 
        
        if "/video/" in resolved_link.lower():
            await processing_message.edit_text("Este é um link de vídeo, não de produto. 😥\n\nPor favor, envie o link correto do produto. Use o /tutorial para saber como fazer.")
            return

        # ATUALIZAÇÃO: Adicionado "-i." à lista de padrões de links válidos.
        if "/product/" not in resolved_link.lower() and "/item/" not in resolved_link.lower() and "affiliation-i." not in resolved_link.lower() and "-i." not in resolved_link.lower():
            await processing_message.edit_text("Este link não parece ser de um produto. 😕\n\nPor favor, copie o link novamente e me envie. Consulte o /tutorial se tiver dúvidas.")
            return

        video_db = context.bot_data['video_db']
        normalized_link = resolved_link.split('?')[0]

        if normalized_link in video_db:
            existing_video_link = video_db[normalized_link]
            await processing_message.edit_text(f"Já temos um vídeo para este produto! 🎬\n\nAssista aqui: {existing_video_link}")
        else:
            link_data = {'user_id': user_id, 'original_link': resolved_link, 'normalized_link': normalized_link}
            context.bot_data.setdefault('link_queue', []).append(link_data)
            await processing_message.edit_text("Obrigado! O seu produto foi adicionado à fila para análise. ✅")

            fila_atual = context.bot_data.get('link_queue', [])
            nova_quantidade = len(fila_atual)
            if nova_quantidade > 0 and nova_quantidade % 6 == 0:
                mensagem_notificacao = f"🔔 Alerta! A fila de pendentes atingiu {nova_quantidade} produtos. Usem /add6 para processar o lote."
                for admin_id in ADMIN_IDS:
                    try:
                        await context.bot.send_message(chat_id=admin_id, text=mensagem_notificacao)
                    except Exception as e:
                        print(f"Falha ao notificar o admin {admin_id}: {e}")
    else:
        # --- FLUXO DE SUPORTE ---
        username = f"@{user.username}" if user.username else "Não tem"
        
        magic_id_string = f"\n\n[support_id={user.id}]"

        forward_message = (
            f"📩 **Nova mensagem de suporte de {user.first_name}**\n\n"
            f"**Username:** {username}\n"
            f"---------------------------------\n"
            f"{message_text}\n"
            f"---------------------------------\n"
            f"Para responder, use a função 'Responder' (Reply) do Telegram nesta mensagem."
            f"{magic_id_string}"
        )

        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(chat_id=admin_id, text=forward_message)
            except Exception as e:
                print(f"Falha ao encaminhar mensagem para o admin {admin_id}: {e}")
                
        await update.message.reply_text("✅ A sua mensagem foi enviada para o suporte. Responderemos assim que possível aqui mesmo no chat.")

