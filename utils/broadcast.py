import logging
from telegram import Update, ContextTypes
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters
from database.db_manager import db_manager
from config import is_admin, BROADCAST_MESSAGE

logger = logging.getLogger(__name__)

# --- Broadcast Handlers ---

async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Broadcast process shuru karta hai (sirf Admin ke liye)."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ **Access Denied**. Aapko is command ka access nahi hai.")
        return ConversationHandler.END

    await update.message.reply_text(
        "📢 **Broadcast Mode On**. Ab woh message bhejo jise sab users ko bhejna hai.\n"
        "Cancel karne ke liye /cancel type karo."
    )
    return BROADCAST_MESSAGE

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Received message ko saare users ko bhejta hai."""
    message_to_send = update.message.text
    
    user_ids_to_send = db_manager.get_all_user_ids()
    
    success_count = 0
    fail_count = 0
    
    for user_id in user_ids_to_send:
        try:
            if user_id != update.effective_user.id:
                await context.bot.send_message(user_id, f"📢 **Broadcast Message**:\n\n{message_to_send}", parse_mode='Markdown')
                success_count += 1
        except Exception as e:
            logger.error(f"Failed to send broadcast to {user_id}: {e}")
            fail_count += 1

    await update.message.reply_text(
        f"✅ **Broadcast Complete!**\n"
        f"Safalta: {success_count} users tak pahuncha.\n"
        f"Asafalta (Blocked/Error): {fail_count}"
    )
    return ConversationHandler.END

async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Broadcast process ko cancel karta hai."""
    await update.message.reply_text("Broadcast cancel kar diya gaya.")
    return ConversationHandler.END

# Broadcast Conversation Handler
broadcast_handler = ConversationHandler(
    entry_points=[CommandHandler("broadcast", broadcast_start)],
    states={
        BROADCAST_MESSAGE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_message)
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel_broadcast)],
)
