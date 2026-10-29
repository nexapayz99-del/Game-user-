from motor.motor_asyncio import AsyncIOMotorClient

# Connect to MongoDB
db_client = AsyncIOMotorClient("mongodb://localhost:27017")
db = db_client["word_game_db"]
sessions_collection = db["sessions"]

# Pre-load your word seek dictionary categorized by length
WORD_DICT = {
    3: ["cat", "dog", "sun", "car"],
    4: ["moon", "star", "bird", "fish"],
    5: ["apple", "mango", "water", "earth"],
    6: ["planet", "rocket", "forest", "orange"],
    7: ["quantum", "gravity", "network", "desktop"],
    8: ["universe", "software", "database", "keyboard"],
    9: ["algorithm", "developer", "framework", "asynchron"],
}

async def save_session(user_id, phone, session_string):
    await sessions_collection.update_one(
        {"user_id": user_id},
        {"$set": {"phone": phone, "session": session_string}},
        upsert=True
    )

async def get_all_sessions():
    return await sessions_collection.find({}).to_list(length=None)
