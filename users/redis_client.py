import redis
from django.conf import settings

redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True,
)

CONFIRMATION_CODE_TTL = 300


def set_confirmation_code(user_id: int, code: str) -> None:
    key = f'confirmation_code:{user_id}'
    redis_client.set(key, code, ex=CONFIRMATION_CODE_TTL)


def get_confirmation_code(user_id: int):
    key = f'confirmation_code:{user_id}'
    return redis_client.get(key)


def delete_confirmation_code(user_id: int) -> None:
    key = f'confirmation_code:{user_id}'
    redis_client.delete(key)