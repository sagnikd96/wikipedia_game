from flask.ext.login import UserMixin

USER_FILE = "user_file.dat"

def parse_user_file(filename):
    user_database = {}
    for line in open(filename):
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
