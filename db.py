"""MongoDB persistence for runner state and operational events."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError

log = logging.getLogger(__name__)

class Database:
    def __init__(self, uri: str, db_name: str):
        self.client = AsyncIOMotorClient(
            uri,
            serverSelectionTimeoutMS=8000,
            connectTimeoutMS=8000,
            socketTimeoutMS=15000,
            retryWrites=True,
        )
        self.db = self.client[db_name]
        self.settings = self.db["settings"]
        self.events = self.db["events"]

    async def connect(self) -> None:
        await self.client.admin.command("ping")
        await self.settings.update_one(
            {"_id": "runner"},
            {"$setOnInsert": {"paused": False, "updated_at": self._now()}},
            upsert=True,
        )
        await self.events.create_index("created_at", expireAfterSeconds=60 * 60 * 24 * 30)
        log.info("MongoDB connection verified")

    @staticmethod
    def _now():
        return datetime.now(timezone.utc)

    async def is_paused(self) -> bool:
        doc = await self.settings.find_one({"_id": "runner"}, {"paused": 1})
        return bool(doc and doc.get("paused", False))

    async def set_paused(self, paused: bool, actor_id: int) -> None:
        await self.settings.update_one(
            {"_id": "runner"},
            {"$set": {
                "paused": paused,
                "updated_at": self._now(),
                "updated_by": actor_id,
            }},
            upsert=True,
        )
        await self.log_event("runner_paused" if paused else "runner_resumed", actor_id=actor_id)

    async def log_event(self, event: str, **fields) -> None:
        try:
            await self.events.insert_one({
                "event": event,
                "created_at": self._now(),
                **fields,
            })
        except PyMongoError:
            log.exception("Could not write operational event: %s", event)

    async def close(self) -> None:
        self.client.close()
