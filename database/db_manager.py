import os
import logging
from pymongo import MongoClient
from config import MONGO_URI, ADMIN_ID # Config se import kiya

logger = logging.getLogger(__name__)

class MongoDBManager:
    """Saare MongoDB connections aur operations ko manage karta hai."""
    
    def __init__(self):
        if not MONGO_URI:
            logger.error("❌ MONGO_URI environment variable set nahi hai.")
            raise ValueError("MONGO_URI missing.")

        try:
            self._client = MongoClient(MONGO_URI)
            self._db = self._client['telegram_quizbot']
            
            self.users_col = self._db['users']
            self.questions_col = self._db['questions']
            
            self.users_col.create_index("user_id", unique=True)
            logger.info("✅ MongoDB connection successful.")
            
            self._populate_initial_questions()
            
        except Exception as e:
            logger.error(f"❌ MongoDB connection error: {e}")
            raise

    # --- Utility: Initial Data ---

    def _populate_initial_questions(self):
        """Default questions daalte hain agar collection empty ho."""
        if self.questions_col.count_documents({}) == 0:
            initial_questions = [
                {"q_id": 1, "text": "Bharat ki rajdhani?", "options": ["Mumbai", "Delhi", "Kolkata"], "answer": "Delhi"},
                {"q_id": 2, "text": "CPU ka full form?", "options": ["Control Processing Unit", "Central Processing Unit", "Computer Power Unit"], "answer": "Central Processing Unit"},
                {"q_id": 3, "text": "Python kisne banayi?", "options": ["Guido van Rossum", "Elon Musk", "Mark Zuckerberg"], "answer": "Guido van Rossum"},
            ]
            # q_id ko index bana dete hain
            for i, q in enumerate(initial_questions):
                 q['q_id'] = i + 1
            self.questions_col.insert_many(initial_questions)
            logger.info("➕ Initial questions added.")

    # --- User/Score Functions ---
    
    def get_or_create_user(self, user_id: int, username: str):
        """User ko fetch karta hai, agar nahi hai toh naya create karta hai."""
        user_data = self.users_col.find_one({"user_id": user_id})
        
        if not user_data:
            new_user = {
                "user_id": user_id,
                "username": username,
                "score": 0,
                "last_q_id": 0, 
                "is_admin": user_id == ADMIN_ID # Admin check
            }
            self.users_col.insert_one(new_user)
            return new_user
        return user_data

    def update_user_score_and_progress(self, user_id: int, q_id: int, points: int):
        """User ka score aur last_q_id update karta hai."""
        self.users_col.update_one(
            {"user_id": user_id},
            {"$set": {"last_q_id": q_id}, "$inc": {"score": points}}
        )

    # --- Quiz Functions ---

    def get_next_question(self, last_q_id: int):
        """Next question fetch karta hai (sequence mein)."""
        next_q_id = last_q_id + 1
        
        question = self.questions_col.find_one({"q_id": next_q_id})
        
        # Agar next question na mile, toh first question wapas bhejenge
        if not question:
             return self.questions_col.find_one({"q_id": 1})
        
        return question

    def get_question_by_id(self, q_id: int):
        """ID se question fetch karta hai."""
        return self.questions_col.find_one({"q_id": q_id})

    # --- Leaderboard & Broadcast Functions ---
    
    def get_top_users(self, limit: int = 10):
        """Score ke descending order mein top users fetch karta hai."""
        return list(self.users_col.find().sort("score", -1).limit(limit))

    def get_all_user_ids(self):
        """Broadcast ke liye sabhi user IDs fetch karta hai."""
        return [doc['user_id'] for doc in self.users_col.find({}, {"user_id": 1})]

# Global instance
db_manager = MongoDBManager()
