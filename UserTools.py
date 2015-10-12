from flask.ext.login import UserMixin
from itertools import takewhile
import RedisConnect as rc
import logic as lg

USER_FILE = "user_file.dat"

def decomment(filename, comment="#"):
    f = lambda x: x != comment
    for line in open(filename):
        yield "".join(takewhile(f, line))

def parse_user_file(filename, comment="#"):
    user_database = {}
    for line in decomment(filename, comment):
        try:
            name, display_name, password_hash = tuple(map(lambda x: x.strip(), line.strip().split(",")))
            user_database[name] = (name, display_name, password_hash)
        except ValueError:
            pass
    return user_database

class User(UserMixin):
    # Create user database here
    user_database = parse_user_file(USER_FILE)

    def __init__(self, name, display_name, password_hash):
        self.name = name
        self.display_name = display_name
        self.password_hash = password_hash

    def get_id(self):
        return self.name

    @classmethod
    def get(cls,name):
        """
        Returns the name if name is a valid user, else, returns None
        """
        if name in User.user_database:
            return name
        else:
            return None

    @classmethod
    def get_password_hash(cls, name):
        """
        Returns the password hash
        """
        if name in User.user_database:
            return User.user_database[name][2]
        else:
            return None

def generate_user_stats(username, user_pool):
    user_info = rc.get_user_from_redis(username, user_pool)
    user_stats = {}
    user_stats['display_name'] = User.user_database[username][1]
    user_stats['current_points'] = lg.UserLogic.scoreFromTuple(user_info)
    user_stats['starting_points'] = user_info[1]
    user_stats['points_for_solving'] = user_info[2]
    user_stats['points_for_selling'] = user_info[3]
    user_stats['expenditure'] = user_info[4]
    user_stats['problems_solved'] = user_info[5]
    user_stats['solutions_bought'] = user_info[6]
    user_stats['solutions_sold'] = user_info[7]
    return user_stats
