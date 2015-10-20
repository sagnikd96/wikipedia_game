from logic import Problem, UserLogic, Commodity
from RedisLocks import RedisWriteLock
import redis

RETRY_INTERVAL = 0.01
EXPIRE_TIME = 2

def get_user_from_redis(user, connection_pool):
    connection = redis.Redis(connection_pool=connection_pool)
    with RedisWriteLock(connection, user, RETRY_INTERVAL, EXPIRE_TIME):
        try:
            result = UserLogic.fromString(connection.get(user).decode())
            return result
        except AttributeError:
            return None

def get_problem_from_redis(problem_id, problem_pool):
    connection = redis.Redis(connection_pool=problem_pool)
    with RedisWriteLock(connection, problem_id, RETRY_INTERVAL, EXPIRE_TIME):
        result = Problem.fromString(connection.get(problem_id).decode())
        return result

def submit_solution(solution, problem_id, problem_pool):
    connection = redis.Redis(connection_pool=problem_pool)
    with RedisWriteLock(connection, problem_id, RETRY_INTERVAL, EXPIRE_TIME):
        problem = Problem.fromString(connection.get(problem_id).decode())
        result = problem.submit_solution(solution)
        connection.set(problem_id, str(problem))
        return result

def update_user_solution(points, problem_id, user_id, user_pool):
    connection = redis.Redis(connection_pool=user_pool)
    with RedisWriteLock(connection, user_id, RETRY_INTERVAL, EXPIRE_TIME):
        user_info = UserLogic.fromString(connection.get(user_id).decode())
        if problem_id in user_info[5]:
            return False
        else:
            user_info[5].append(problem_id)
            user_info[2] += points
            connection.set(user_id, UserLogic.toString(user_info))
            return True
