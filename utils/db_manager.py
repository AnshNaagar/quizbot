# utils/db_manager.py (MongoDB Version)

import os
import logging
from pymongo import MongoClient
from bson.objectid import ObjectId # MongoDB IDs ke liye

logger = logging.getLogger(__name__)

MONGO_URI = os.getenv("DATABASE_URL")
DB_NAME = "quiz" # Jo MongoDB Atlas mein database ka naam rakha hai

def get_db_connection():
    """MongoDB Atlas se connection establish karta hai."""
    if not MONGO_URI:
        logger.error("DATABASE_URL environment variable is not set!")
        return None
    try:
        # Pymongo client
        client = MongoClient(MONGO_URI)
        # Connection check (optional but good practice)
        client.admin.command('ping') 
        db = client[DB_NAME]
        return db 
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        return None

# ----------------------------------------------------------------------
# 2. CRUD & Fetching Functions
# ----------------------------------------------------------------------

def fetch_categories(db):
    """Categories collection se data fetch karta hai."""
    # MongoDB mein collections se saara data nikalna
    # _id ko exclude karna zaroori hai
    return list(db.categories.find({}, {"_id": 0}).sort("name_en", 1))

def save_new_session(db, user_id, category_id, language, total_questions):
    """Naya quiz session sessions collection mein save karta hai."""
    session_data = {
        "user_id": user_id,
        "category_id": category_id,
        "language": language,
        "total_questions": total_questions,
        "current_score": 0,
        "questions_asked": [], # Question IDs ki list
        "status": "active"
    }
    result = db.sessions.insert_one(session_data)
    # MongoDB _id ko string mein convert karke return karna zaroori hai
    return str(result.inserted_id)

def fetch_active_session_and_question_details(db, user_id):
    """User ki latest active session aur us session ka aakhri question details nikalta hai."""
    # Latest active session dhoondho
    session_data = db.sessions.find_one(
        {"user_id": user_id, "status": "active"},
        sort=[('_id', -1)] # Latest session
    )

    if not session_data or not session_data.get('questions_asked'):
        return None, None, None

    session_id = str(session_data['_id'])
    current_score = session_data['current_score']
    
    # Aakhri question ID nikalna
    latest_question_id = session_data['questions_asked'][-1]

    # Question details aur correct answer nikalna
    question = db.questions.find_one({"question_id": latest_question_id})
    
    if question:
        correct_answer_index = question.get('correct_option_id')
        return session_id, current_score, correct_answer_index
    
    return None, None, None


def update_session_score(db, session_id, new_score):
    """Active quiz session ka score update karta hai."""
    try:
        # ObjectId use karna zaroori hai _id field ke liye
        db.sessions.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": {"current_score": new_score}}
        )
        return new_score
    except Exception as e:
        logger.error(f"Error updating score for session {session_id}: {e}")
        return None
