# Производительность: кеширование и rate limiting

Сервис заказа поездок (вариант из ДЗ №3–4). Стек: FastAPI, MongoDB, Redis.

## 1. Анализ производительности

### Hot paths

| Операция | Нагрузка |
|----------|----------|
| `GET /users/by-login/{login}` | Проверка клиента при каждом сценарии |
| `GET /trips/active` | Дашборд водителей, частые опросы |
| `POST /trips` | Создание заказа, пиковая нагрузка |

### Медленные операции

- Запросы в MongoDB (`find`, `find_one`, агрегации по regex в search)
- Сортировка и фильтрация активных поездок по индексу `{status, created_at}`

### Требования

| Метрика | Цель |
|---------|------|
| p95 `GET` (кеш hit) | < 50 ms |
| p95 `GET` (кеш miss) | < 200 ms |
| `POST /trips` | < 300 ms при нормальной нагрузке |
| Пропускная способность read | ≥ 500 RPS на инстанс (с Redis) |

## 2. Стратегия кеширования

| Данные | Паттерн | TTL | Инвалидация |
|--------|---------|-----|-------------|
| Профиль по логину (`user:login:*`) | **Cache-Aside** | 300 с | Не требуется (профиль не меняется в API) |
| Список активных поездок (`trips:active`) | **Cache-Aside** | 30 с | `DELETE` при `POST /trips`, `accept`, `complete` |

**Почему Cache-Aside:** приложение само читает/пишет кеш; при падении Redis API продолжает работать через MongoDB.

**Почему не Write-Through/Back:** запись поездки редкая относительно чтения; проще сбросить ключ после мутации.

### Инвалидация

- Явная: удаление `trips:active` после изменения статуса поездки
- TTL: страховка при пропущенной инвалидации

## 3. Rate limiting

| Endpoint | Алгоритм | Лимит | Ключ |
|----------|----------|-------|------|
| `POST /trips` | **Sliding Window Counter** (Redis ZSET) | 100/мин (обычный), 1000/мин (`X-User-Tier: premium`) | IP клиента |

**Почему Sliding Window:** ровнее, чем Fixed Window (нет «двойного» всплеска на границе минуты), проще Sliding Window Log.

**Заголовки ответа:** `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` (unix). При превышении — `429 Too Many Requests`.

Другие endpoints без лимита: read-heavy, кеш снижает нагрузку; `POST /users` — редкий.

## 4. Влияние на систему

**Кеширование**

- Снижает нагрузку на MongoDB и latency read-запросов
- `trips:active` убирает повторные scan по статусу при опросе водителями

**Rate limiting**

- Защищает `POST /trips` от злоупотреблений и перегрузки БД
- Гарантирует справедливое распределение ресурсов между клиентами

## 5. Метрики мониторинга

| Метрика | Назначение |
|---------|------------|
| `cache_hits_total`, `cache_misses_total` | Hit rate по ключам |
| `http_request_duration_seconds` (p50/p95) | Latency с/без кеша |
| `rate_limit_rejected_total` | Частота 429 |
| `mongodb_op_duration_seconds` | Нагрузка на БД |
| `redis_connected` | Доступность кеша |

### Hit rate

```
hit_rate = cache_hits / (cache_hits + cache_misses)
```

Считать по endpoint (Prometheus counters в middleware) или через `redis INFO` + логирование `X-Cache: HIT|MISS` (опционально).

Целевой hit rate: ≥ 80% для `by-login`, ≥ 60% для `trips/active` при типичном трафике.
