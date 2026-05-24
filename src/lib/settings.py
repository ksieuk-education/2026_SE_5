from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/taxi/v1"
    mongo_host: str = "localhost"
    mongo_port: int = 27017
    mongo_db: str = "taximongo"
    redis_host: str = "localhost"
    redis_port: int = 6379
    cache_user_ttl: int = 300
    cache_active_trips_ttl: int = 30
    rate_limit_window: int = 60
    rate_limit_trips: int = 100
    rate_limit_trips_premium: int = 1000

    def mongo_uri(self) -> str:
        return f"mongodb://{self.mongo_host}:{self.mongo_port}"

    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"
