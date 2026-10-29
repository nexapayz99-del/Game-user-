import os
import asyncio
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
import uvloop

# Load environment variables from .env file
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
TARGET_GROUP = int(os.getenv("TARGET_GROUP"))

# Import your database functions and word dictionary
from db import get_all_sessions, WORD_DICT 

async def run_userbots():
    sessions = await get_all_sessions()
    clients = []

    if not sessions:
        print("No accounts found in MongoDB.")
        return

    for data in sessions:
        client = Client(
            f"user_{data['user_id']}",
            session_string=data["session"],
            api_id=API_ID,
            api_hash=API_HASH
        )
        
        @client.on_message(filters.chat(TARGET_GROUP) & filters.text)
        async def word_seek_handler(c, message):
            text = message.text.lower()
            target_length = None
            
            # Detect requested word length from the game bot's message
            for length in range(3, 10):
                if f"{length} letter" in text or f"length: {length}" in text:
                    target_length = length
                    break
            
            # Guess ALL words of that length
            if target_length and target_length in WORD_DICT:
                words_to_guess = WORD_DICT[target_length]
                
                for guess in words_to_guess:
                    try:
                        await message.reply_text(guess.upper())
                        # 1.5 second delay prevents rapid-fire spam bans
                        await asyncio.sleep(1.5) 
                    except FloodWait as e:
                        print(f"Hit rate limit. Sleeping for {e.value} seconds.")
                        await asyncio.sleep(e.value)
                    except Exception as e:
                        print(f"Error sending word: {e}")

        clients.append(client)

    print(f"Starting {len(clients)} userbots...")
    await asyncio.gather(*[c.start() for c in clients])
    
    from pyrogram import idle
    await idle()
    
    await asyncio.gather(*[c.stop() for c in clients])

if __name__ == "__main__":
    uvloop.install()
    asyncio.run(run_userbots())
