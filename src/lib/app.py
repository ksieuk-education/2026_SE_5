from contextlib import asynccontextmanager
from typing import Any

from bson import ObjectId
from fastapi import APIRouter, FastAPI, HTTPException, Query, Request, Response
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError
from redis.asyncio import Redis

from lib.cache import Cache
from lib.domain import TripStatus
from lib.ratelimit import RateLimiter
from lib.repos import TripRepo, UserRepo
from lib.schemas import TripAccept, TripCreate, TripOut, UserCreate, UserOut
from lib.settings import Settings

ACTIVE_TRIPS_KEY = "trips:active"


def user_out(doc: dict[str, Any]) -> UserOut:
    return UserOut(
        id=str(doc["_id"]),
        login=doc["login"],
        first_name=doc["first_name"],
        last_name=doc["last_name"],
    )


def trip_out(doc: dict[str, Any]) -> TripOut:
    return TripOut(
        id=str(doc["_id"]),
        user_id=str(doc["user_id"]),
        driver_id=str(doc["driver_id"]) if doc.get("driver_id") else None,
        status=TripStatus(doc["status"]),
        created_at=doc.get("created_at"),
    )


def get_db(request: Request) -> AsyncIOMotorDatabase[Any]:
    return request.app.state.db


def get_cache(request: Request) -> Cache:
    return request.app.state.cache


def get_limiter(request: Request) -> RateLimiter:
    return request.app.state.limiter


def client_key(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def trip_limit(request: Request, settings: Settings) -> int:
    if request.headers.get("X-User-Tier", "").lower() == "premium":
        return settings.rate_limit_trips_premium
    return settings.rate_limit_trips


router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/users", status_code=201)
async def create_user(body: UserCreate, request: Request) -> UserOut:
    repo = UserRepo(get_db(request))
    try:
        doc = await repo.create(body.login.strip(), body.first_name.strip(), body.last_name.strip())
    except DuplicateKeyError as exc:
        raise HTTPException(409, "логин занят") from exc
    return user_out(doc)


@router.get("/users/by-login/{login}")
async def user_by_login(login: str, request: Request) -> UserOut:
    key = f"user:login:{login.strip()}"
    cache = get_cache(request)
    cached = await cache.get(key)
    if cached:
        return UserOut.model_validate(cached)

    doc = await UserRepo(get_db(request)).by_login(login.strip())
    if doc is None:
        raise HTTPException(404, "не найден")
    out = user_out(doc)
    await cache.set(key, out.model_dump(), request.app.state.settings.cache_user_ttl)
    return out


@router.get("/users/search")
async def search_users(request: Request, name_mask: str = Query(min_length=1)) -> list[UserOut]:
    docs = await UserRepo(get_db(request)).search(name_mask.strip())
    return [user_out(d) for d in docs]


@router.post("/trips", status_code=201)
async def create_trip(body: TripCreate, request: Request, response: Response) -> TripOut:
    settings: Settings = request.app.state.settings
    limit = trip_limit(request, settings)
    ok, remaining, reset = await get_limiter(request).check(
        f"trips:create:{client_key(request)}",
        limit,
        settings.rate_limit_window,
    )
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(reset)
    if not ok:
        raise HTTPException(
            429,
            "слишком много запросов",
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset),
            },
        )

    db = get_db(request)
    user = await db["users"].find_one({"_id": ObjectId(body.user_id)})
    if user is None:
        raise HTTPException(404, "пользователь не найден")
    doc = await TripRepo(db).create(user)
    await get_cache(request).delete(ACTIVE_TRIPS_KEY)
    return trip_out(doc)


@router.get("/trips/active")
async def active_trips(request: Request) -> list[TripOut]:
    cache = get_cache(request)
    cached = await cache.get(ACTIVE_TRIPS_KEY)
    if cached is not None:
        return [TripOut.model_validate(t) for t in cached]

    docs = await TripRepo(get_db(request)).list_active()
    out = [trip_out(d) for d in docs]
    settings: Settings = request.app.state.settings
    await cache.set(
        ACTIVE_TRIPS_KEY,
        [t.model_dump(mode="json") for t in out],
        settings.cache_active_trips_ttl,
    )
    return out


@router.get("/users/{user_id}/trips/history")
async def trip_history(user_id: str, request: Request) -> list[TripOut]:
    docs = await TripRepo(get_db(request)).history(user_id)
    return [trip_out(d) for d in docs]


@router.post("/trips/{trip_id}/accept")
async def accept_trip(trip_id: str, body: TripAccept, request: Request) -> TripOut:
    doc = await TripRepo(get_db(request)).accept(trip_id, body.driver_id)
    if doc is None:
        raise HTTPException(409, "заказ недоступен")
    await get_cache(request).delete(ACTIVE_TRIPS_KEY)
    return trip_out(doc)


@router.post("/trips/{trip_id}/complete")
async def complete_trip(trip_id: str, request: Request) -> TripOut:
    doc = await TripRepo(get_db(request)).complete(trip_id)
    if doc is None:
        raise HTTPException(409, "поездка не active")
    await get_cache(request).delete(ACTIVE_TRIPS_KEY)
    return trip_out(doc)


def create_app(settings: Settings) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        mongo = AsyncIOMotorClient(settings.mongo_uri())
        redis = Redis.from_url(settings.redis_url(), decode_responses=True)
        app.state.mongo = mongo
        app.state.db = mongo[settings.mongo_db]
        app.state.redis = redis
        app.state.cache = Cache(redis)
        app.state.limiter = RateLimiter(redis)
        app.state.settings = settings
        yield
        await redis.aclose()
        mongo.close()

    app = FastAPI(title="Taxi API", lifespan=lifespan)
    app.include_router(router, prefix=settings.api_prefix)
    return app
