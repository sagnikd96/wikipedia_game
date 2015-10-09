import redis
from UserTools import USER_FILE, parse_user_file
from RedisConf import HOSTNAME, PORT, USER_DB, PROBLEM_DB
from logic import UserLogic
from ProblemTools import parseProblemFile, PROBLEM_FILE

STARTING_POINTS = 100

user_pool = redis.ConnectionPool(host=HOSTNAME, port=PORT, db=USER_DB)
problem_pool = redis.ConnectionPool(host=HOSTNAME, port=PORT, db=PROBLEM_DB)

def load_users_to_redis(filename, comment="#"):
    user_database = parse_user_file(USER_FILE, comment)
    connection = redis.Redis(connection_pool = user_pool)
    for user in user_database:
        current_user = str(UserLogic(user, STARTING_POINTS))
        connection.set(user, current_user)
    connection.set("__initiated__", "True")

def load_problems_to_redis(filename, comment="#"):
    problem_database = parseProblemFile(PROBLEM_FILE)
    connection = redis.Redis(connection_pool = problem_pool)
    for problem in problem_database:
        connection.set(problem, problem_database[problem])
    connection.set("__initiated__", "True")

def check_database_initiated(pool):
    connection = redis.Redis(connection_pool = pool)
    if connection.get("__initiated__") == b'True':
        return True
    else:
        return False

def delete_all_locks(pools):
    for pool in pools:
        connection = redis.Redis(connection_pool = pool)
        keys = list(map(lambda x: x.decode() + "_lock", connection.keys()))
        for key in keys:
            connection.delete(key)

if __name__=="__main__":
    from sys import argv
    load_users_to_redis(argv[-1])
