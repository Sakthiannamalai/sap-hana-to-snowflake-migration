import redis
from app.config.env_loader import get_env_variable

REDIS_HOST = get_env_variable('REDIS_HOST', 'localhost')
REDIS_PORT = int(get_env_variable('REDIS_PORT', 6379))
REDIS_DB = int(get_env_variable('REDIS_DB', 0))

redis_client = redis.StrictRedis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True
)

