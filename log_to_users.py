from datetime import datetime
from flask_conf import LOG_DIRECTORY

def write_to_file(filename, string):
    with open(filename, "a") as log:
        log.write(string)

def time_now():
    now = datetime.now()
    timestamp = "{0}:{1}:{2}-{3}/{4}/{5}".format(now.hour, now.minute, now.second, now.day, now.month, now.year)
    return timestamp

def submission_string(user_id, problem_id, points):
    timestamp = time_now()
    return "[{0}] {1} solved {2}. Obtained {3} points".format(timestamp, user_id, problem_id, points)

def purchase_string(buyer_id, seller_id, problem_id, price, points):
    timestamp = time_now()
    return "[{0}] {1} bought {2} from {3} for {4} points. Got {5} points.".format(timestamp, buyer_id, problem_id, seller_id, price, points)

def on_market_string(seller_id, problem_id, price, charges):
    timestamp = time_now()
    return "[{0}] {1} put up {2} for {3} points. Was charged {4} points".format(timestamp, seller_id, problem_id, price, charges)

def changed_price_string(seller_id, problem_id, price, charges):
    timestamp = time_now()
    return "[{0}] {1} changed the price of {2} to {3} points. Was charged {4} points.".format(timestamp, seller_id, problem_id, price, charges)


def log_submission(user_id, problem_id, points):
    filename = "{0}{1}.log".format(LOG_DIRECTORY, user_id)
    string = submission_string(user_id, problem_id, points) + '\n'
    write_to_file(filename, string)

def log_purchase(buyer_id, seller_id, problem_id, price, points):
    filename = "{0}{1}.log".format(LOG_DIRECTORY, buyer_id)
    string = purchase_string(buyer_id, seller_id, problem_id, price, points) + '\n'
    write_to_file(filename, string)

def log_on_market(seller_id, problem_id, price, charges):
    filename = "{0}{1}.log".format(LOG_DIRECTORY, seller_id)
    string = on_market_string(seller_id, problem_id, price, charges) + '\n'
    write_to_file(filename, string)

def log_changed_price(seller_id, problem_id, price, charges):
    filename = "{0}{1}.log".format(LOG_DIRECTORY, seller_id)
    string = changed_price_string(seller_id, problem_id, price, charges) + '\n'
    write_to_file(filename, string)
