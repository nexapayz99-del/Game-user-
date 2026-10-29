from motor.motor_asyncio import AsyncIOMotorClient

db_client = AsyncIOMotorClient("mongodb://localhost:27017")
db = db_client["word_game_db"]
sessions_collection = db["sessions"]
settings_collection = db["settings"]

# Word dictionary (expand this as needed)
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

async def get_bot_status():
    status = await settings_collection.find_one({"_id": "bot_status"})
    if status is None:
        return True # Default to active
    return status.get("is_active", True)

async def set_bot_status(is_active: bool):
    await settings_collection.update_one(
        {"_id": "bot_status"},
        {"$set": {"is_active": is_active}},
        upsert=True
    )
