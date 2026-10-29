"""Single-owner Pyrogram game assistant with a separate control bot."""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import re
import signal
import time
from contextlib import suppress

from dotenv import load_dotenv
from pyrogram import Client, filters, idle
from pyrogram.errors import FloodWait, RPCError
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery

from db import Database
from words import choose_word

load_dotenv()

def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value

def parse_config():
    api_id_raw = required("API_ID")
    if not api_id_raw.isdigit():
        raise ValueError("API_ID must be numeric")
    api_id = int(api_id_raw)
    api_hash = required("API_HASH")
    bot_token = required("BOT_TOKEN")
    user_session = required("USER_SESSION")
    mongo_uri = required("MONGO_URI")
    mongo_db = os.getenv("MONGO_DB", "game_user").strip() or "game_user"
    group_raw = required("TARGET_GROUP_ID")
    try:
        target_group_id = int(group_raw)
    except ValueError as exc:
        raise ValueError("TARGET_GROUP_ID must be a numeric Telegram chat ID") from exc
    admin_raw = required("ADMIN_IDS")
    try:
        admin_ids = {int(x.strip()) for x in admin_raw.split(",") if x.strip()}
    except ValueError as exc:
        raise ValueError("ADMIN_IDS must contain comma-separated numeric Telegram user IDs") from exc
    if not admin_ids:
        raise ValueError("ADMIN_IDS must contain at least one admin ID")
    sender_username = os.getenv("GAME_BOT_USERNAME", "").strip().lstrip("@").lower()
    interval_raw = os.getenv("SEND_INTERVAL_SECONDS", "5").strip()
    try:
        interval = max(5.0, float(interval_raw))
    except ValueError as exc:
        raise ValueError("SEND_INTERVAL_SECONDS must be a number") from exc
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    return {
        "api_id": api_id,
        "api_hash": api_hash,
        "bot_token": bot_token,
        "user_session": user_session,
        "mongo_uri": mongo_uri,
        "mongo_db": mongo_db,
        "target_group_id": target_group_id,
        "admin_ids": admin_ids,
        "sender_username": sender_username,
        "send_interval": interval,
        "log_level": log_level,
    }

PROMPT_PATTERNS = [
    re.compile(r"\bfind\s+(?:a\s+)?(\d{1,2})\s*[- ]?\s*letter\s+word\b", re.I),
    re.compile(r"\b(\d{1,2})\s*[- ]?\s*letter\s+word\b", re.I),
    re.compile(r"\bword\s+(?:with|having)\s+(\d{1,2})\s+letters?\b", re.I),
    re.compile(r"\bword\s+of\s+length\s+(\d{1,2})\b", re.I),
    re.compile(r"\blength\s*:\s*(\d{1,2})\b", re.I),
]

def extract_length(text: str) -> int | None:
    for pattern in PROMPT_PATTERNS:
        match = pattern.search(text)
        if match:
            length = int(match.group(1))
            if 2 <= length <= 20:
                return length
    return None

class App:
    def __init__(self, cfg):
        self.cfg = cfg
        self.db = Database(cfg["mongo_uri"], cfg["mongo_db"])
        self.control_bot = Client(
            "game_control_bot",
            api_id=cfg["api_id"],
            api_hash=cfg["api_hash"],
            bot_token=cfg["bot_token"],
        )
        self.user_client = Client(
            "game_owner_account",
            api_id=cfg["api_id"],
            api_hash=cfg["api_hash"],
            session_string=cfg["user_session"],
        )
        self.send_lock = asyncio.Lock()
        self.last_send_at = 0.0
        self.stopping = asyncio.Event()
        self.register_handlers()

    def is_admin(self, user_id: int | None) -> bool:
        return user_id is not None and user_id in self.cfg["admin_ids"]

    def controls_keyboard(self):
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("▶️ Resume", callback_data="runner:resume"),
                InlineKeyboardButton("⏸ Pause", callback_data="runner:pause"),
            ],
            [InlineKeyboardButton("🔄 Status", callback_data="runner:status")],
        ])

    def register_handlers(self):
        @self.control_bot.on_message(filters.private & filters.command(["start", "help", "status", "pause", "resume"]))
        async def command_handler(_, message: Message):
            uid = message.from_user.id if message.from_user else None
            command = (message.command or [""])[0].lower()
            if command == "start" or command == "help":
                if not self.is_admin(uid):
                    await message.reply_text("This control panel is restricted to authorized administrators.")
                    return
                await message.reply_text(
                    "Game Runner Control Panel\n\n"
                    "/status — show runner state\n"
                    "/pause — pause replies\n"
                    "/resume — resume replies\n\n"
                    "Use the buttons below to control the runner.",
                    reply_markup=self.controls_keyboard(),
                )
                return
            if not self.is_admin(uid):
                await message.reply_text("Not authorized.")
                return
            if command == "status":
                paused = await self.db.is_paused()
                await message.reply_text(
                    f"Runner status: {'⏸ PAUSED' if paused else '▶️ ACTIVE'}\n"
                    f"Target group: {self.cfg['target_group_id']}",
                    reply_markup=self.controls_keyboard(),
                )
            elif command == "pause":
                await self.db.set_paused(True, uid)
                await message.reply_text("⏸ Runner paused.", reply_markup=self.controls_keyboard())
            elif command == "resume":
                await self.db.set_paused(False, uid)
                await message.reply_text("▶️ Runner resumed.", reply_markup=self.controls_keyboard())

        @self.control_bot.on_callback_query()
        async def callback_handler(_, query: CallbackQuery):
            uid = query.from_user.id
            if not self.is_admin(uid):
                await query.answer("Not authorized.", show_alert=True)
                return
            action = (query.data or "").split(":")[-1]
            if action == "pause":
                await self.db.set_paused(True, uid)
                response = "Runner paused."
            elif action == "resume":
                await self.db.set_paused(False, uid)
                response = "Runner resumed."
            elif action == "status":
                paused = await self.db.is_paused()
                response = f"Runner is {'PAUSED' if paused else 'ACTIVE'}."
            else:
                await query.answer("Unknown action.", show_alert=True)
                return
            await query.answer(response)
            with suppress(Exception):
                await query.message.edit_reply_markup(reply_markup=self.controls_keyboard())

        @self.user_client.on_message(filters.chat(self.cfg["target_group_id"]) & filters.text)
        async def game_message_handler(_, message: Message):
            if await self.db.is_paused():
                return
            if not message.text:
                return
            if self.cfg["sender_username"]:
                sender = message.from_user
                username = (sender.username or "").lower() if sender else ""
                if username != self.cfg["sender_username"]:
                    return
            length = extract_length(message.text)
            if length is None:
                return
            word = choose_word(length)
            if not word:
                logging.warning("No dictionary entry for requested length %s", length)
                await self.db.log_event("word_unavailable", length=length, chat_id=message.chat.id)
                return
            try:
                async with self.send_lock:
                    # Re-check pause after waiting for the lock.
                    if await self.db.is_paused():
                        return
                    wait_for = self.cfg["send_interval"] - (time.monotonic() - self.last_send_at)
                    if wait_for > 0:
                        await asyncio.sleep(wait_for)
                    # Do not send if paused while waiting.
                    if await self.db.is_paused():
                        return
                    await self.user_client.send_message(message.chat.id, word, reply_to_message_id=message.id)
                    self.last_send_at = time.monotonic()
                logging.info("Replied to group %s with a %s-letter word", message.chat.id, length)
                await self.db.log_event("word_sent", length=length, chat_id=message.chat.id)
            except FloodWait as exc:
                delay = max(int(exc.value), int(self.cfg["send_interval"]))
                logging.warning("Telegram FloodWait: sleeping %s seconds", delay)
                await self.db.log_event("flood_wait", seconds=delay, chat_id=message.chat.id)
                await asyncio.sleep(delay)
            except RPCError:
                logging.exception("Telegram RPC error while sending game reply")
                await self.db.log_event("send_rpc_error", chat_id=message.chat.id)
            except asyncio.CancelledError:
                raise
            except Exception:
                logging.exception("Unexpected game handler error")
                await self.db.log_event("send_unexpected_error", chat_id=message.chat.id)

    async def run(self):
        await self.db.connect()
        logging.info("Starting control bot and authorized user client")
        await self.control_bot.start()
        try:
            await self.user_client.start()
            me = await self.user_client.get_me()
            logging.info("User client connected as id=%s", me.id)
            logging.info("Target group: %s", self.cfg["target_group_id"])
            await idle()
        finally:
            logging.info("Stopping clients")
            with suppress(Exception):
                await self.user_client.stop()
            with suppress(Exception):
                await self.control_bot.stop()
            await self.db.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-config", action="store_true")
    args = parser.parse_args()
    try:
        cfg = parse_config()
    except Exception as exc:
        print(f"Configuration error: {exc}")
        raise SystemExit(2)
    logging.basicConfig(
        level=getattr(logging, cfg["log_level"], logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    if args.check_config:
        print("Configuration syntax looks valid. Credentials were not tested.")
        return
    app = App(cfg)
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        pass
    except Exception:
        logging.exception("Fatal application error")
        raise SystemExit(1)

if __name__ == "__main__":
    main()
