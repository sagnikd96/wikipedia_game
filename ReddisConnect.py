from logic import Problem, UserLogic, Commodity
from RedisLocks import RedisWriteLock
import redis

def get_user_from_redis(user, connection_pool):
    connection = redis.Redis(connection_pool=connection_pool)
    with RedisWriteLock(connection, user, 0.01, 2):
        result = UserLogic.fromString(connection.get(user).decode())
    return result
