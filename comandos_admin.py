from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import Forbidden
import re
from config import ADMIN_IDS
from database import save_video_db
from api_shopee import convert_shopee_links

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

async def add_links(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    
    if num_to_add > len(fila):
        await update.message.reply_text(f"Pediu {num_to_add} links, mas só existem {len(fila)}.")
        return

    items_to_process = fila[:num_to_add]
    links_for_api = [item['original_link'] for item in items_to_process]
    user_ids_to_notify = list(set([item['user_id'] for item in items_to_process]))
    
    context.user_data['last_processed_items'] = items_to_process
    context.user_data['last_processed_user_ids'] = user_ids_to_notify

    converted_links = convert_shopee_links(links_for_api)
    
    await update.message.reply_text("--- Links Convertidos ---")
    await update.message.reply_text("\n".join(converted_links))

    context.bot_data['link_queue'] = fila[num_to_add:]
    await update.message.reply_text(f"Pronto! {num_to_add} links foram processados. Restam {len(context.bot_data['link_queue'])}.\n\n"
                                    "Agora, crie o vídeo e use o comando:\n`/video <link_do_video>`")

async def pendentes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS: return
    quantidade = len(context.bot_data.get('link_queue', []))
    await update.message.reply_text(f"Existem {quantidade} links pendentes na fila. ⏳")

async def addmanual(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS: return
    context.user_data['state'] = 'awaiting_manual_links'
    context.user_data['manual_links_list'] = []
    await update.message.reply_text("Modo de adição manual ativado. Envie até 6 links. Use /add para processar.")

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS: return
    if context.user_data.get('state') == 'awaiting_manual_links':
        manual_links = context.user_data.get('manual_links_list', [])
        if not manual_links:
            await update.message.reply_text("Nenhum link adicionado. Use /cancelar para sair.")
            return
        
        await update.message.reply_text(f"A processar {len(manual_links)} links manuais...")
        converted_links = convert_shopee_links(manual_links)
        await update.message.reply_text("--- Links Convertidos (Adição Manual) ---")
        await update.message.reply_text("\n".join(converted_links))

        manual_items = [{'original_link': link, 'normalized_link': link.split('?')[0]} for link in manual_links]
        context.user_data['last_processed_items'] = manual_items
        context.user_data['last_processed_user_ids'] = [update.effective_user.id]
        context.user_data.pop('state', None)
        context.user_data.pop('manual_links_list', None)
        await update.message.reply_text("Links manuais processados. Para enviar um vídeo, use `/video <link>`.")
    else:
        await update.message.reply_text("Use /add apenas após o /addmanual.")

async def video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS: return

    if not context.args:
        await update.message.reply_text("Uso correto: /video <link_do_video>")
        return
    
    video_link_original = context.args[0]
    items_processed = context.user_data.get('last_processed_items')

    if not items_processed:
        await update.message.reply_text("Você precisa de processar um lote com /add<N> ou /addmanual primeiro.")
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
    await update.message.reply_text("Base de dados de vídeos atualizada com sucesso! ✅")

    user_ids_to_notify = context.user_data.get('last_processed_user_ids', [])
    
    await update.message.reply_text(f"A iniciar o envio para {len(user_ids_to_notify)} utilizador(es)...")
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
    
    await update.message.reply_text(f"Envio do vídeo concluído!\n\n✅ Sucesso: {sucesso}\n❌ Falha: {falha}")
    
    context.user_data.pop('last_processed_user_ids', None)
    context.user_data.pop('last_processed_items', None)

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id not in ADMIN_IDS: return
    if context.user_data.get('state') == 'awaiting_manual_links':
        context.user_data.clear()
        await update.message.reply_text("Modo de adição manual cancelado.")
    elif 'last_processed_items' in context.user_data:
        items_to_restore = context.user_data.pop('last_processed_items')
        context.bot_data['link_queue'] = items_to_restore + context.bot_data.get('link_queue', [])
        context.user_data.pop('last_processed_user_ids', None)
        await update.message.reply_text(f"Ação desfeita! {len(items_to_restore)} links foram devolvidos à fila.")
    else:
        await update.message.reply_text("Não há nenhuma operação recente para cancelar.")

async def enviar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS: return

    if not context.args:
        await update.message.reply_text("Uso correto: /enviar <sua mensagem aqui>")
        return
    
    message_to_send = " ".join(context.args)
    all_user_ids = context.bot_data.get('user_ids', set())
    
    if not all_user_ids:
        await update.message.reply_text("Nenhum utilizador registado para receber a mensagem.")
        return

    sucesso = 0
    falha = 0
    await update.message.reply_text(f"A iniciar o envio da mensagem para {len(all_user_ids)} utilizadores... Isso pode levar um tempo.")

    for uid in all_user_ids:
        try:
            await context.bot.send_message(chat_id=uid, text=message_to_send)
            sucesso += 1
        except Exception as e:
            falha += 1
            print(f"Falha ao enviar para o ID {uid}: {e}")

    await update.message.reply_text(f"Envio concluído!\n\n✅ Sucesso: {sucesso}\n❌ Falha: {falha}")

async def esgotado(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await handle_problematic_link(update, context, "esgotado")

async def bugado(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await handle_problematic_link(update, context, "bugado")

async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processa mensagens de texto de admins, especialmente respostas a pedidos de suporte."""
    if update.message.reply_to_message and update.message.reply_to_message.from_user.is_bot:
        replied_text = update.message.reply_to_message.text
        
        # CORREÇÃO: Procura pelo novo "código de ID" que é 100% fiável.
        match = re.search(r"\[support_id=(\d+)\]", replied_text)
        
        if match:
            target_user_id = int(match.group(1))
            reply_text = update.message.text
            
            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=f"✉️ **Resposta do Suporte:**\n\n{reply_text}"
                )
                await update.message.reply_text(f"✅ A sua resposta foi enviada para o utilizador `{target_user_id}`.")
            except Forbidden:
                error_message = (
                    f"❌ Falha ao enviar a mensagem para o ID `{target_user_id}`.\n\n"
                    "**Motivos prováveis:**\n"
                    "1. O utilizador **nunca iniciou uma conversa** com o bot (peça-lhe para enviar /start).\n"
                    "2. O utilizador **bloqueou** o bot."
                )
                await update.message.reply_text(error_message)
            except Exception as e:
                print(f"Falha ao responder ao ID {target_user_id}: {e}")
                await update.message.reply_text(f"❌ Ocorreu um erro inesperado ao tentar enviar a mensagem para o ID `{target_user_id}`.")
            return

    if context.user_data.get('state') == 'awaiting_manual_links':
        manual_links = context.user_data['manual_links_list']
        if len(manual_links) < 6:
            manual_links.append(update.message.text)
            await update.message.reply_text(f"Link {len(manual_links)}/6 adicionado. Use /add para processar.")
        else:
            await update.message.reply_text("Limite de 6 links atingido. Use /add para processar.")
    else:
        await update.message.reply_text("Comando ou mensagem não reconhecido. Use uma das opções do menu ou responda a um pedido de suporte.")

