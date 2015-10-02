import redis
from time import sleep

class RedisLock(): # Sticking to this. Hope doesn't lead to a deadlock.
    def __init__(self, redis_connection, param, waiting_interval = 0.01, ttl = None):
        self.redis_connection = redis_connection
        self.param = param
        self.lock = param + "_lock"
        self.waiting_interval = waiting_interval
        self.ttl = ttl

    def __enter__(self):
        while not self.redis_connection.setnx(self.lock, "taken"):
            sleep(self.waiting_interval)
        if self.ttl:
            self.redis_connection.expire(self.lock, self.ttl)

    def __exit__(self, type, value, traceback):
        self.redis_connection.delete(self.lock)

class RedisWriteLock():
    def __init__(self, redis_connection, param, waiting_interval = 0.01, ttl = None):
        self.redis_connection = redis_connection
        self.param = param
        self.write_lock = param + "_write_lock"
        self.read_lock = param + "_read_lock"
        self.waiting_interval = waiting_interval
        self.ttl = ttl

    def __enter__(self):
        while not self.redis_connection.setnx(self.write_lock, "taken"):
            sleep(self.waiting_interval)
        while not self.redis_connection.setnx(self.read_lock, "taken"):
            sleep(self.waiting_interval)
        if self.ttl:
            self.redis_connection.expire(self.write_lock, self.ttl)
            self.redis_connection.expire(self.read_lock, self.ttl)

    def __exit__(self, type, value, traceback):
        self.redis_connection.delete(self.read_lock)
        self.redis_connection.delete(self.write_lock)

class RedisReadLock(): # Not sure if this leads to a deadlock? Kinda risky. Will stick to the other lock for now.
    def __init__(self, redis_connection, param, waiting_interval = 0.01, ttl = None):
        self.redis_connection = redis_connection
        self.param = param
        self.write_lock = param + "_write_lock"
        self.read_lock = param + "_read_lock"
        self.delete_lock = param + "_delete_lock"
        self.waiting_interval = waiting_interval
        self.ttl = ttl

    def __enter__(self):
        while not self.redis_connection.setnx(self.write_lock, "taken"):
            sleep(self.waiting_interval)
        while not self.redis_connection.setnx(self.delete_lock, "taken"):
            sleep(self.waiting_interval)
        self.redis_connection.delete(self.delete_lock)
        self.redis_connection.push(self.read_lock, "queued")
        redis_connection.delete(self.write_lock)

    def __exit__(self, type, value, traceback):
        while not self.redis_connection.setnx(self.delete_lock):
            sleep(self.waiting_interval)
        result = self.redis_connection.pop(self.read_lock)
        if result == None:
            self.redis_connection.delete(self.read_lock)
        self.redis_connection.delete(self.delete_lock)
