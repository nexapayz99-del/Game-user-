import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

import pyromod.listen
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid
from db import save_session, get_all_sessions, get_bot_status, set_bot_status

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_GROUP = int(os.getenv("TARGET_GROUP"))

app = Client("login_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def get_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Account", callback_data="add_account")],
        [InlineKeyboardButton("🎮 Start Game in Group", callback_data="start_game_group")],
        [InlineKeyboardButton("▶️ Resume Guessing", callback_data="resume_bot"),
         InlineKeyboardButton("⏸ Pause Guessing", callback_data="pause_bot")]
    ])

@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    await message.reply_text(
        "**Word Game Controller Menu**\nChoose an action below:",
        reply_markup=get_main_menu()
    )

@app.on_callback_query()
async def callback_handler(client, cq):
    data = cq.data
    chat_id = cq.message.chat.id

    if data == "pause_bot":
        await set_bot_status(False)
        await cq.answer("⏸ Auto-guessing paused!", show_alert=True)
    
    elif data == "resume_bot":
        await set_bot_status(True)
        await cq.answer("▶️ Auto-guessing resumed!", show_alert=True)

    elif data == "start_game_group":
        # Uses the first saved account to send the start command to the game group
        sessions = await get_all_sessions()
        if not sessions:
            await cq.answer("⚠️ Add an account first!", show_alert=True)
            return
            
        await cq.answer("Sending start command to group...", show_alert=False)
        
        try:
            temp_client = Client(
                "temp_starter", 
                session_string=sessions[0]["session"], 
                api_id=API_ID, 
                api_hash=API_HASH, 
                in_memory=True
            )
            await temp_client.connect()
            # Replace "/start_game" with the actual command required to start the game
            await temp_client.send_message(TARGET_GROUP, "/start_game")
            await temp_client.disconnect()
            await cq.message.reply_text("✅ Sent start command to the target group.")
        except Exception as e:
            await cq.message.reply_text(f"❌ Failed to start game: {e}")

    elif data == "add_account":
        await cq.answer()
        try:
            phone_msg = await client.ask(chat_id, "Send the phone number (with country code):", timeout=60)
            phone_number = phone_msg.text.strip()

            temp_client = Client(f"temp_{chat_id}", api_id=API_ID, api_hash=API_HASH, in_memory=True)
            await temp_client.connect()

            sent_code = await temp_client.send_code(phone_number)
            
            otp_msg = await client.ask(chat_id, "Send the OTP code (numbers only):", timeout=60)
            otp = otp_msg.text.replace(" ", "")

            try:
                await temp_client.sign_in(phone_number, sent_code.phone_code_hash, otp)
            except SessionPasswordNeeded:
                pwd_msg = await client.ask(chat_id, "Send your 2FA password:", timeout=60)
                await temp_client.check_password(pwd_msg.text)
            
            session_string = await temp_client.export_session_string()
            await save_session(chat_id, phone_number, session_string)
            await temp_client.disconnect()
            
            await cq.message.reply_text("✅ Account successfully added to database!")
        except Exception as e:
            await cq.message.reply_text(f"❌ Login failed: {e}")

if __name__ == "__main__":
    print("Login Bot Running...")
    app.run()
