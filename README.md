# Сервис такси — ДЗ №5 (кеш и rate limiting)

Добавлены: кэш + rate limit

## Запуск

```bash
cp .env.example .env
docker compose up -d --build
```

- API: http://localhost:8002/api/taxi/v1/health  
- Swagger: http://localhost:8002/docs  
- MongoDB и Redis

## Примеры

```bash
# кеш: первый запрос — miss (Mongo), повторный — hit (Redis)
curl http://localhost:8002/api/taxi/v1/users/by-login/client1
curl http://localhost:8002/api/taxi/v1/trips/active

# rate limit на создание поездки (100/мин, premium — 1000/мин)
curl -X POST http://localhost:8002/api/taxi/v1/trips \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"674a10000000000000000001"}' -i

curl -X POST http://localhost:8002/api/taxi/v1/trips \
  -H 'Content-Type: application/json' \
  -H 'X-User-Tier: premium' \
  -d '{"user_id":"674a10000000000000000001"}' -i
```

Инвалидация кеша активных поездок — при `POST /trips`, `POST /trips/{id}/accept`, `POST /trips/{id}/complete`.

## Оптимизации

| Что | Где |
|-----|-----|
| Cache-Aside, TTL 300 с | `GET /users/by-login/{login}` |
| Cache-Aside, TTL 30 с + инвалидация | `GET /trips/active` |
| Sliding Window rate limit | `POST /trips` |

Подробнее: [`performance_design.md`](performance_design.md).

## Локально

```bash
cd src
poetry install --no-root
MONGO_HOST=localhost REDIS_HOST=localhost poetry run python -m bin
```

Нужны `docker compose up -d taxi-mongo taxi-redis`.

```bash
poetry run ruff check .
```

## Структура

```
src/lib/app.py — роуты, кеш, лимиты
src/lib/cache.py — Redis cache-aside
src/lib/ratelimit.py — sliding window (ZSET)
```
