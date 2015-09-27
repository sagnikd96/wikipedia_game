from flask.ext.login import UserMixin

MARKET_FEE_NEW_ITEM = 5
MARKET_FEE_CHANGE_PRICE = 5

class Problem():
    def __init__(self, name, answer, base_points, multiplier):
        self.name = name
        self.answer = answer
        self.base_points = base_points
        self.multiplier = multiplier
        self.times_solved = 1
        self.points = base_points

    def submit_solution(self, solution):
        if solution == self.answer:
            self.times_solved += 1
            points_to_award = self.points
            self.points = round(self.points * self.multiplier)
            return (True, points_to_award)
        else:
            return (False, 0)


class User(UserMixin):
    # Create user database here
    user_database = {"test": ("test", "Test Display", "password")}

    def __init__(self, name, display_name, password_hash, starting_points):
        self.name = name
        self.display_name = display_name
        self.password_hash = password_hash
        self.starting_points = starting_points
        self.points_for_solving = 0
        self.points_for_selling = 0
        self.expenditure = 0
        self.problems_solved = [] # List of problems
        self.solutions_bought = [] # List of problems
        self.solutions_sold = [] # List of commodities

    def get_capital(self):
        return self.starting_points + self.points_for_solving + self.points_for_selling - self.expenditure

    def solve_problem(self, problem, solution):
        result, points = problem.submit_solution(solution)
        if result and not problem in self.problems_solved:
            self.problems_solved.append(problem)
            self.points_for_solving += points
            return True
        else:
            return False

    def sell_problem(self, problem, price):
        problems_sold = map(lambda x: x.problem, self.solutions_sold)
        if problem in self.problems_solved and (not problem in problems_sold) and self.get_capital() >= MARKET_FEE_NEW_ITEM:
            self.expenditure += MARKET_FEE_NEW_ITEM
            self.solutions_sold.append(Commodity(problem, self, price))
            return True
        else:
            return False

    def change_price(self, commodity, new_price):
        if commodity in self.solutions_sold and self.get_capital() >= MARKET_FEE_CHANGE_PRICE:
            self.expenditure += MARKET_FEE_CHANGE_PRICE
            new_commodity = Commodity(commodity.problem, self, new_price)
            self.solutions_sold = [new_commodity] + [i for i in self.solutions_sold if i!=commodity]
            return True
        else:
            return False

    def buy_solution(self, commodity):
        problem = commodity.problem
        price = commodity.price
        if not problem in self.problems_solved and self.get_capital() >= price:
            results, points = problem.submit_solution(problem.answer)
            self.problems_solved.append(problem)
            self.points_for_solving += points
            self.expenditure += price
            return True
        else:
            return False

    @classmethod
    def get(cls,name):
        """
        Returns the name if name is a valid user, else, returns None
        """
        if name in User.user_database:
            return name
        else:
            return None

class Commodity():
    def __init__(self, problem, seller, price):
        self.problem = problem
        self.seller = seller
        self.price = price

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.problem.name == other.problem.name and self.seller.name == other.seller.name
        else:
            return False

    def __neq__(self, other):
        return not self.__eq__(other)

    def get_price(self):
        return self.price

    def set_price(self, new_price):
        self.price = new_price

    def purchase(self):
        return (self.problem.answer, self.problem)
