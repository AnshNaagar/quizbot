# main.py

import os
import logging
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    PollAnswerHandler 
)

# Utils se import karein
from utils import db_manager, quiz_logic 

# ----------------------------------------------------------------------
# 1. Configuration & Setup
# ----------------------------------------------------------------------

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
 
# Conversation States
SELECT_CATEGORY, SELECT_LANGUAGE, SELECT_COUNT = range(3)

# Logging Setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# 2. Conversation Handlers (Quiz Setup Flow)
# ----------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """/start command se category selection shuru karta hai."""
    db = db_manager.get_db_connection()
    if not db:
        await update.message.reply_text("Database connection mein problem hai. Kripya baad mein try karein.")
        return ConversationHandler.END

    categories = db_manager.fetch_categories(db) # MongoDB call
    
    if not categories:
        await update.message.reply_text("Koi categories available nahi hain. Kripya admin se sampark karein.")
        return ConversationHandler.END

    keyboard = []
    for i in range(0, len(categories), 3):
        row = [
            # categories mein ab documents hain, list nahi
            InlineKeyboardButton(cat['name_en'], callback_data=f"cat_{cat['category_id']}")
            for cat in categories[i:i+3]
        ]
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        'Welcome! Kripya quiz category chuniye:',
        reply_markup=reply_markup
    )
    return SELECT_CATEGORY

async def select_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # ... (select_category function jaisa pehle tha, ismein koi badlaav nahi) ...
    query = update.callback_query
    await query.answer()

    category_id = int(query.data.split('_')[1])
    context.user_data['selected_category_id'] = category_id

    keyboard = [
        [
            InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"),
            InlineKeyboardButton("Hindi 🇮🇳", callback_data="lang_hi")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"Category chuni gayi. Ab quiz ki bhasha chuniye:",
        reply_markup=reply_markup
    )
    return SELECT_LANGUAGE

async def select_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # ... (select_language function jaisa pehle tha, ismein koi badlaav nahi) ...
    query = update.callback_query
    await query.answer()
    
    language = query.data.split('_')[1]
    context.user_data['selected_language'] = language

    counts = [20, 30, 50, 70, 100]
    keyboard = [[InlineKeyboardButton(f"{count} Questions", callback_data=f"count_{count}") for count in counts]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"Bhasha '{language}' set hai. Ab kitne sawaal ka set chahiye (20-100)?",
        reply_markup=reply_markup
    )
    return SELECT_COUNT

async def start_quiz_set(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Session save karke quiz set shuru karta hai aur pehla poll schedule karta hai."""
    query = update.callback_query
    await query.answer()

    question_count = int(query.data.split('_')[1])
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    
    category_id = context.user_data.get('selected_category_id')
    language = context.user_data.get('selected_language')

    db = db_manager.get_db_connection()
    if not db:
        await query.edit_message_text("Database connection failed. Session shuru nahi ho paya.")
        return ConversationHandler.END

    # MongoDB call
    session_id = db_manager.save_new_session(db, user_id, category_id, language, question_count)
    
    if not session_id:
        await query.edit_message_text("Session save karte waqt error aa gayi.")
        return ConversationHandler.END

    await query.edit_message_text(
        f"Bahut khoob! Quiz set ({question_count} sawaal) shuru ho raha hai... Pehla sawal jaldi hi aayega!"
    )
    
    # Job Queue shuru karein jo pehla poll bhejega!
    context.application.job_queue.run_once(
        quiz_logic.send_next_quiz_poll, 
        1, 
        context={
            'chat_id': chat_id, 
            'session_id': session_id,
            'category_id': category_id,
            'language': language
        },
        name=f"quiz_{session_id}_1"
    )

    context.user_data.clear() 
    return ConversationHandler.END


# ----------------------------------------------------------------------
# 3. Poll Answer Handler (Scoring Logic)
# ----------------------------------------------------------------------

async def handle_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User ke poll answer ko process karta hai aur score update karta hai."""
    poll_answer = update.poll_answer
    user_id = poll_answer.user.id
    
    user_answer_index = poll_answer.option_ids[0] if poll_answer.option_ids else None
    
    if user_answer_index is None:
        return 

    db = db_manager.get_db_connection()
    if not db:
        logger.error("DB connection error in poll handler.")
        return
        
    # MongoDB call
    session_id, current_score, correct_answer_index = \
        db_manager.fetch_active_session_and_question_details(db, user_id)

    if session_id is None:
        return

    is_correct = (user_answer_index == correct_answer_index)
    
    if is_correct:
        new_score = current_score + 1
        db_manager.update_session_score(db, session_id, new_score) # MongoDB call
        logger.info(f"User {user_id} scored point. New score: {new_score}")
    else:
        logger.info(f"User {user_id} answered incorrectly.")

# ----------------------------------------------------------------------
# 4. Main Runner
# ----------------------------------------------------------------------

def main() -> None:
    """Bot ko run karta hai aur handlers register karta hai."""
    
    application = Application.builder().token(TOKEN).build()
    
    quiz_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_CATEGORY: [CallbackQueryHandler(select_category, pattern='^cat_')],
            SELECT_LANGUAGE: [CallbackQueryHandler(select_language, pattern='^lang_')],
            SELECT_COUNT: [CallbackQueryHandler(start_quiz_set, pattern='^count_')],
        },
        fallbacks=[CommandHandler('start', start)],
    )

    application.add_handler(quiz_conv_handler)
    application.add_handler(PollAnswerHandler(handle_poll_answer))
    
    logger.info("Bot polling shuru kar raha hai...")
    application.run_polling(poll_interval=3)

if __name__ == '__main__':
    main()
