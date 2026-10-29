import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

from pyrogram import Client, filters
from pyrogram.errors import FloodWait
import uvloop
from db import get_all_sessions, get_bot_status, WORD_DICT 

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
TARGET_GROUP = int(os.getenv("TARGET_GROUP"))

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
            # Check if bot is paused via the UI
            is_active = await get_bot_status()
            if not is_active:
                return

            text = message.text.lower()
            target_length = None
            
            # Detect requested word length from the game bot's message
            for length in range(3, 10):
                if f"{length} letter" in text or f"length: {length}" in text:
                    target_length = length
                    break
            
            if target_length and target_length in WORD_DICT:
                words_to_guess = WORD_DICT[target_length]
                
                # Guess words with a strict 5-second delay
                for guess in words_to_guess:
                    # Check status again mid-loop in case you paused it while it was guessing
                    if not await get_bot_status():
                        break 
                        
                    try:
                        await message.reply_text(guess.upper())
                        await asyncio.sleep(5.0) # 5 SECOND GAP PREVENTS RATE LIMITS
                        
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
