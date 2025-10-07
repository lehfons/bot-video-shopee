from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown
import re
from config import ADMIN_IDS
from api_shopee import convert_shopee_links, resolve_short_link
from database import save_video_db

async def add_links(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processa links da fila e os envia formatados para o admin."""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS: return

    try:
        num_to_add = int(update.message.text.replace("/add", ""))
    except ValueError:
        await update.message.reply_text("Comando inválido.")
        return

    fila = context.bot_data.get('link_queue', [])
    if not fila:
        await update.message.reply_text("A fila de links dos utilizadores está vazia. ✅")
        return
    
    # Garante que não processamos mais links do que os que existem na fila
    num_to_process = min(num_to_add, len(fila))
    items_to_process = fila[:num_to_process]
    
    links_for_api = [item['original_link'] for item in items_to_process]
    user_ids_to_notify = list(set([item['user_id'] for item in items_to_process]))
    
    context.user_data['last_processed_items'] = items_to_process
    context.user_data['last_processed_user_ids'] = user_ids_to_notify

    await update.message.reply_text(f"A converter {num_to_process} links, por favor aguarde...")
    converted_links = convert_shopee_links(links_for_api)
    
    number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣"]
    formatted_message = "*Produtos do lote para vídeo:*\n"
    for i, link in enumerate(converted_links):
        link_escaped = escape_markdown(link, version=2)
        if "Erro" in link:
             formatted_message += f"❌ {link_escaped}\n"
        elif i < len(number_emojis):
            formatted_message += f"{number_emojis[i]} {link_escaped}\n"
        else:
            formatted_message += f"{i+1}\\. {link_escaped}\n"
    
    await update.message.reply_text(formatted_message, parse_mode=ParseMode.MARKDOWN_V2)

    context.bot_data['link_queue'] = fila[num_to_process:]
    # CORREÇÃO: Adicionada formatação e escape de caracteres
    mensagem_final = (
        f"Pronto\! {num_to_process} links foram processados\. Restam {len(context.bot_data['link_queue'])}\.\n\n"
        "Agora, crie o vídeo e use o comando:\n`/video <link_do_video>`"
    )
    await update.message.reply_text(mensagem_final, parse_mode=ParseMode.MARKDOWN_V2)

async def pendentes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Informa o admin sobre a quantidade de links na fila principal."""
    if update.effective_user.id not in ADMIN_IDS: return
    quantidade = len(context.bot_data.get('link_queue', []))
    await update.message.reply_text(f"Existem {quantidade} links pendentes na fila. ⏳")

async def addmanual(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Inicia o modo de adição manual interativo."""
    if update.effective_user.id not in ADMIN_IDS: return
    context.user_data['state'] = 'awaiting_manual_links'
    context.user_data['manual_links_original'] = []
    context.user_data['manual_links_converted'] = []
    await update.message.reply_text(
        "Modo de adição manual ativado.\n\n"
        "Use `/add <link>` para adicionar até 6 links ao seu lote.\n"
        "Quando terminar, use `/video <link_do_video>` para finalizar."
    )

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Adiciona um link ao lote manual ou converte um link individualmente."""
    if update.effective_user.id not in ADMIN_IDS: return

    user_state = context.user_data.get('state')
    
    if user_state == 'awaiting_manual_links':
        if not context.args:
            await update.message.reply_text("Por favor, forneça um link para adicionar. Ex: `/add https://...`")
            return

        original_list = context.user_data.get('manual_links_original', [])
        if len(original_list) >= 6:
            await update.message.reply_text("Limite de 6 links atingido. Use `/video <link>` para finalizar ou /cancelar.")
            return

        link_to_add = context.args[0]
        
        msg = await update.message.reply_text(f"A adicionar e converter o link...")
        resolved_link = resolve_short_link(link_to_add)
        converted_link_list = convert_shopee_links([resolved_link])
        
        if not converted_link_list or "Erro" in converted_link_list[0]:
            error_msg = converted_link_list[0] if converted_link_list else 'Erro desconhecido'
            await msg.edit_text(f"Falha ao converter o link: {error_msg}")
            return

        converted_link = converted_link_list[0]
        
        context.user_data.setdefault('manual_links_original', []).append(resolved_link)
        context.user_data.setdefault('manual_links_converted', []).append(converted_link)

        converted_list = context.user_data['manual_links_converted']
        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣"]
        formatted_message = "*Produtos do lote manual para vídeo:*\n"
        for i, link in enumerate(converted_list):
            link_escaped = escape_markdown(link, version=2)
            if i < len(number_emojis):
                formatted_message += f"{number_emojis[i]} {link_escaped}\n"
            else:
                formatted_message += f"{i+1}\\. {link_escaped}\n"
        
        await msg.edit_text(formatted_message, parse_mode=ParseMode.MARKDOWN_V2)

        if len(converted_list) == 6:
            await update.message.reply_text("Limite de 6 links atingido. Use `/video <link>` para finalizar o lote.")

    elif context.args:
        link_to_convert = context.args[0]
        await update.message.reply_text("A converter o link...")
        resolved_link = resolve_short_link(link_to_convert)
        converted_link_list = convert_shopee_links([resolved_link])
        
        if converted_link_list and "Erro" not in converted_link_list[0]:
            link_escaped = escape_markdown(converted_link_list[0], version=2)
            formatted_message = f"*Link convertido:*\n1️⃣ {link_escaped}"
            await update.message.reply_text(formatted_message, parse_mode=ParseMode.MARKDOWN_V2)
        else:
            error_msg = converted_link_list[0] if converted_link_list else 'Erro desconhecido'
            await update.message.reply_text(f"Falha ao converter o link: {error_msg}")
    else:
        await update.message.reply_text(
            "Uso do comando /add:\n\n"
            "1. Após usar `/addmanual`, para processar o lote.\n"
            "2. Para converter um link na hora: `/add <link_da_shopee>`"
        )

async def video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Converte um link de vídeo e envia para os utilizadores do último lote (manual ou da fila)."""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS: return

    if not context.args:
        await update.message.reply_text("Uso correto: /video <link_do_video>")
        return
    
    video_link_original = context.args[0]
    items_processed = None
    user_ids_to_notify = None

    if context.user_data.get('state') == 'awaiting_manual_links' or 'manual_links_original' in context.user_data:
        original_manual_links = context.user_data.get('manual_links_original', [])
        if not original_manual_links:
            await update.message.reply_text("Você não adicionou nenhum link ao lote manual. Use `/add <link>` primeiro.")
            return
        items_processed = [{'original_link': link, 'normalized_link': link.split('?')[0]} for link in original_manual_links]
        user_ids_to_notify = [user_id]
    
    elif 'last_processed_items' in context.user_data:
        items_processed = context.user_data.get('last_processed_items')
        user_ids_to_notify = context.user_data.get('last_processed_user_ids')

    if not items_processed:
        await update.message.reply_text("Você precisa de processar um lote com /add<N> ou iniciar um com /addmanual primeiro.")
        return

    await update.message.reply_text("A converter o link do vídeo...")
    converted_video_link_list = convert_shopee_links([video_link_original])

    if not converted_video_link_list or "Erro" in converted_video_link_list[0]:
        await update.message.reply_text(f"Falha ao converter o link do vídeo. A API respondeu: {converted_video_link_list[0]}")
        return
    
    converted_video_link = converted_video_link_list[0]
    
    video_db = context.bot_data['video_db']
    for item in items_processed:
        normalized_product_link = item['normalized_link']
        video_db[normalized_product_link] = converted_video_link
    save_video_db(video_db)
    
    if not user_ids_to_notify:
        await update.message.reply_text("Nenhum utilizador para notificar.")
    else:
        sucesso = 0
        falha = 0
        for uid in user_ids_to_notify:
            try:
                mensagem = f"O vídeo do(s) produto(s) que você enviou está pronto! 🎬\n\nAssista aqui: {converted_video_link}"
                await context.bot.send_message(chat_id=uid, text=mensagem)
                sucesso += 1
            except Exception as e:
                falha += 1
                print(f"Falha ao enviar vídeo para o ID {uid}: {e}")
        
        link_escaped = escape_markdown(converted_video_link, version=2)
        if falha > 0:
            mensagem_final = (
                f"⚠️ *Envio concluído com {falha} falha(s)*\.\n\n"
                f"✅ Sucesso: {sucesso}\n"
                f"❌ Falha: {falha}\n\n"
                f"*Link do vídeo gerado:*\n{link_escaped}"
            )
        else:
            mensagem_final = (
                f"✅ *Sucesso\!* Os utilizadores foram notificados\! 🎉\n\n"
                f"*Link do vídeo gerado:*\n{link_escaped}"
            )
        
        await update.message.reply_text(mensagem_final, parse_mode=ParseMode.MARKDOWN_V2)
    
    context.user_data.clear()

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancela a operação atual: ou o modo manual, ou a última extração da fila."""
    if update.effective_user.id not in ADMIN_IDS: return

    if context.user_data.get('state') == 'awaiting_manual_links':
        context.user_data.clear()
        await update.message.reply_text("Modo de adição manual cancelado.")
    elif 'last_processed_items' in context.user_data:
        items_to_restore = context.user_data.pop('last_processed_items')
        context.bot_data['link_queue'] = items_to_restore + context.bot_data.get('link_queue', [])
        context.user_data.pop('last_processed_user_ids', None)
        await update.message.reply_text(f"Ação desfeita! ✅\n{len(items_to_restore)} links foram devolvidos ao início da fila de pendentes.")
    else:
        await update.message.reply_text("Não há nenhuma operação recente para cancelar.")

async def enviar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envia uma mensagem (texto ou imagem com legenda) para todos os utilizadores registados."""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return

    message = update.message
    photo_id = None
    message_to_send = ""

    if message.photo:
        photo_id = message.photo[-1].file_id
        caption = message.caption or ""
        command_entity = next((entity for entity in message.caption_entities if entity.type == 'bot_command' and caption[entity.offset:entity.offset+entity.length].startswith('/enviar')), None)
        
        if command_entity:
            command_end_offset = command_entity.offset + command_entity.length
            message_to_send = caption[command_end_offset:].lstrip()
        else:
            await update.message.reply_text("Para enviar uma imagem para todos, use o comando /enviar na legenda da imagem.")
            return
    else:
        command_entity = message.entities[0]
        full_text = message.text
        command_end_offset = command_entity.offset + command_entity.length
        message_to_send = full_text[command_end_offset:].lstrip()

    if not message_to_send and not photo_id:
        await update.message.reply_text("Uso: /enviar <texto> ou envie uma imagem com /enviar <legenda>.")
        return
    
    all_user_ids = context.bot_data.get('user_ids', set())
    
    if not all_user_ids:
        await update.message.reply_text("Nenhum utilizador registado para receber a mensagem.")
        return

    sucesso = 0
    falha = 0
    await update.message.reply_text(f"A iniciar o envio para {len(all_user_ids)} utilizadores...")

    for uid in all_user_ids:
        try:
            if photo_id:
                await context.bot.send_photo(chat_id=uid, photo=photo_id, caption=message_to_send)
            else:
                await context.bot.send_message(chat_id=uid, text=message_to_send)
            sucesso += 1
        except Exception as e:
            falha += 1
            print(f"Falha ao enviar para o ID {uid}: {e}")

    await update.message.reply_text(f"Envio concluído!\n\n✅ Sucesso: {sucesso}\n❌ Falha: {falha}")

async def deletar_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Deleta um vídeo da base de dados, desvinculando todos os produtos associados."""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return

    if not context.args:
        await update.message.reply_text("Uso correto: /deletarvideo <link_do_video_a_remover>")
        return
    
    video_link_to_delete = context.args[0]
    video_db = context.bot_data.get('video_db', {})
    
    keys_to_delete = [key for key, value in video_db.items() if value == video_link_to_delete]
    
    if not keys_to_delete:
        await update.message.reply_text("Nenhum produto encontrado na base de dados associado a este link de vídeo.")
        return
        
    for key in keys_to_delete:
        del video_db[key]
        
    save_video_db(video_db)
    
    await update.message.reply_text(
        f"Vídeo removido com sucesso! ✅\n\n"
        f"{len(keys_to_delete)} link(s) de produto(s) foram desvinculados e voltarão para a fila de pendentes se enviados novamente."
    )

async def esgotado(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lida com links esgotados."""
    await handle_problematic_link(update, context, "esgotado")

async def bugado(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lida com links bugados."""
    await handle_problematic_link(update, context, "bugado")

async def handle_problematic_link(update: Update, context: ContextTypes.DEFAULT_TYPE, problem_type: str):
    """Função genérica para lidar com links esgotados ou bugados."""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS: return

    if not context.args:
        await update.message.reply_text(f"Uso correto: /{problem_type} <link_do_produto>")
        return
    
    if 'last_processed_items' not in context.user_data:
        await update.message.reply_text("Não há um lote de produtos a ser verificado. Use /add<N> primeiro.")
        return

    problematic_link_admin = context.args[0]
    normalized_link_admin = problematic_link_admin.split('?')[0]
    
    items_processed = context.user_data['last_processed_items']
    item_found = None
    
    for item in items_processed:
        if item['normalized_link'] == normalized_link_admin:
            item_found = item
            break
    
    if item_found:
        user_to_notify = item_found['user_id']
        
        if problem_type == "esgotado":
            message_to_user = "O produto que você enviou está esgotado. 😕\nObrigado pela sua contribuição!"
        else: # bugado
            message_to_user = "O produto que você enviou não é aceite pela Shopee para ser incluído em vídeos. 😥\nObrigado pela sua contribuição!"

        try:
            await context.bot.send_message(chat_id=user_to_notify, text=message_to_user)
            
            items_processed.remove(item_found)
            user_ids_to_notify = list(set([i['user_id'] for i in items_processed]))
            context.user_data['last_processed_user_ids'] = user_ids_to_notify
            
            await update.message.reply_text(f"Produto marcado como {problem_type}! ✅\nO utilizador {user_to_notify} foi notificado.")
        except Exception as e:
            await update.message.reply_text(f"Falha ao notificar o utilizador {user_to_notify}. Erro: {e}")
    else:
        await update.message.reply_text("Este link não foi encontrado no último lote de produtos processados.")

async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processa mensagens de administradores, principalmente para responder a pedidos de suporte."""
    message = update.message

    if message.reply_to_message and "📩 *Nova mensagem de suporte de" in message.reply_to_message.text:
        original_text = message.reply_to_message.text
        
        match = re.search(r"\[support_id=(\d+)\]", original_text)
        
        if match:
            user_id_to_reply = int(match.group(1))
            try:
                # CORREÇÃO: Adiciona formatação à resposta do suporte
                response_text = f"📨 *Resposta do Suporte:*\n\n{escape_markdown(message.text, version=2)}"
                await context.bot.send_message(
                    chat_id=user_id_to_reply,
                    text=response_text,
                    parse_mode=ParseMode.MARKDOWN_V2
                )
                await update.message.reply_text("✅ A sua resposta foi enviada ao utilizador.")
            except Exception as e:
                error_text = (
                    "❌ *Falha ao enviar a resposta*\.\n\n"
                    "*Possíveis causas:*\n"
                    "1\. O utilizador pode ter bloqueado o bot\.\n"
                    "2\. O utilizador nunca iniciou uma conversa privada com o bot \(envie\-lhe o link do bot e peça para ele enviar /start\)\."
                )
                await update.message.reply_text(error_text, parse_mode=ParseMode.MARKDOWN_V2)
            return

    await update.message.reply_text("Comando ou mensagem não reconhecido. Use uma das opções do menu ou responda a um pedido de suporte.")

