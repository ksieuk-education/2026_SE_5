from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument


class UserRepo:
    def __init__(self, db: AsyncIOMotorDatabase[Any]) -> None:
        self.col = db["users"]

    async def create(self, login: str, first_name: str, last_name: str) -> dict[str, Any]:
        doc = {
            "login": login,
            "first_name": first_name,
            "last_name": last_name,
            "password_hash": "",
            "phones": [],
            "roles": ["passenger"],
            "created_at": datetime.now(UTC),
        }
        result = await self.col.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    async def by_login(self, login: str) -> dict[str, Any] | None:
        return await self.col.find_one({"login": login})

    async def search(self, mask: str) -> list[dict[str, Any]]:
        pat = {"$regex": mask, "$options": "i"}
        cur = self.col.find({"$or": [{"first_name": pat}, {"last_name": pat}]})
        return await cur.to_list(100)


class TripRepo:
    def __init__(self, db: AsyncIOMotorDatabase[Any]) -> None:
        self.col = db["trips"]

    async def create(self, user: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(UTC)
        doc = {
            "user_id": user["_id"],
            "driver_id": None,
            "client": {
                "login": user["login"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
            },
            "status": "pending",
            "route": {"from": "не указано", "to": "не указано"},
            "tags": [],
            "events": [{"at": now, "type": "created"}],
            "created_at": now,
        }
        result = await self.col.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    async def list_active(self) -> list[dict[str, Any]]:
        cur = self.col.find({"status": {"$in": ["pending", "active"]}}).sort("created_at", -1)
        return await cur.to_list(200)

    async def history(self, user_id: str) -> list[dict[str, Any]]:
        cur = self.col.find({"user_id": ObjectId(user_id), "status": "completed"}).sort(
            "created_at", -1
        )
        return await cur.to_list(200)

    async def accept(self, trip_id: str, driver_id: str) -> dict[str, Any] | None:
        return await self.col.find_one_and_update(
            {"_id": ObjectId(trip_id), "status": "pending"},
            {
                "$set": {"status": "active", "driver_id": ObjectId(driver_id)},
                "$push": {"events": {"at": datetime.now(UTC), "type": "accepted"}},
            },
            return_document=ReturnDocument.AFTER,
        )

    async def complete(self, trip_id: str) -> dict[str, Any] | None:
        return await self.col.find_one_and_update(
            {"_id": ObjectId(trip_id), "status": "active"},
            {
                "$set": {"status": "completed"},
                "$push": {"events": {"at": datetime.now(UTC), "type": "completed"}},
            },
            return_document=ReturnDocument.AFTER,
        )
