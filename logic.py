MARKET_FEE_NEW_ITEM = 5
MARKET_FEE_CHANGE_PRICE = 5

class Problem():
    def __init__(self, name, display_name, answer, base_points, multiplier, dependencies):
        self.name = name
        self.display_name = display_name
        self.answer = answer
        self.base_points = base_points
        self.multiplier = multiplier
        self.times_solved = 0
        self.points = base_points
        self.dependencies = dependencies # list of problem names

    def get_id(self):
        return name

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name and \
               self.display_name == other.display_name and \
               self.answer == other.answer and \
               self.base_points == other.base_points and \
               self.multiplier == other.multiplier and \
               self.times_solved == other.times_solved and \
               self.points == other.points and \
               self.dependencies == other.dependencies
        else:
            return False

    def __neq__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return ", ".join([self.name,
                          self.display_name,
                          self.answer,
                          str(self.base_points),
                          str(self.multiplier),
                          str(self.times_solved),
                          str(self.points),
                          "{" + " : ".join(self.dependencies) + "}"
                          ])

    @staticmethod
    def fromString(string):
        components = string.split(", ")
        name = components[0]
        display_name = components[1]
        answer = components[2]
        base_points = int(components[3])
        multiplier = float(components[4])
        times_solved = int(components[5])
        points = int(components[6])
        dependencies = list(filter(lambda x: x != '', components[7][1:-1].split(" : ")))
        problem = Problem(name, display_name, answer, base_points, multiplier, dependencies)
        problem.times_solved = times_solved
        problem.points = points
        return problem

    def submit_solution(self, solution):
        if solution == self.answer:
            self.times_solved += 1
            points_to_award = self.points
            self.points = round(self.points * self.multiplier)
            return (True, points_to_award)
        else:
            return (False, 0)

class UserLogic():

    def __init__(self, name, starting_points):
        self.name = name
        #self.display_name = display_name
        self.starting_points = starting_points
        self.points_for_solving = 0
        self.points_for_selling = 0
        self.expenditure = 0
        self.problems_solved = [] # List of problems
        self.solutions_bought = [] # List of problems
        self.solutions_sold = [] # List of commodities

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.name == other.name
        else:
            return False

    def __neq__(self, other):
        return not self==other

    def __str__(self):
        f = lambda x: x.name
        string_problems_solved = str(list(map(f, self.problems_solved)))
        string_solutions_bought = str(list(map(f, self.solutions_bought)))
        string_solutions_sold = "[" + " :: ".join(list(map(lambda x: str(x), self.solutions_sold))) + "]"
        return " ::: ".join([self.name,
                #self.display_name,
                str(self.starting_points),
                str(self.points_for_solving),
                str(self.points_for_selling),
                str(self.expenditure),
                string_problems_solved,
                string_solutions_bought,
                string_solutions_sold
                ])


    @staticmethod
    def fromString(string):
        f = lambda x: x[1:-1]

        parts = string.split(" ::: ")
        name = parts[0]
        starting_points = int(parts[1])
        points_for_solving = int(parts[2])
        points_for_selling = int(parts[3])
        expenditure = int(parts[4])

        if parts[5][1:-1] != '':
            problems_solved = list(map(f, parts[5][1:-1].split(", ")))
        else:
            problems_solved = []

        if parts[6][1:-1] != '':
            solutions_bought = list(map(f, parts[6][1:-1].split(", ")))
        else:
            solutions_bought = []

        if parts[7][1:-1] != '':
            solutions_sold = list(map(lambda x: Commodity.fromString(x), parts[7][1:-1].split(" :: ")))
        else:
            solutions_sold = []

        return [name, starting_points, points_for_solving, points_for_selling, expenditure, problems_solved, solutions_bought, solutions_sold]

    @staticmethod
    def toString(info_tuple):
        name, starting_points, points_for_solving, points_for_selling, expenditure, problems_solved, solutions_bought, solutions_sold = info_tuple
        string_problems_solved = str(problems_solved)
        string_solutions_bought = str(solutions_bought)
        string_solutions_sold = "[" + " :: ".join(map(lambda x: ", ".join(str(i) for i in x), solutions_sold)) + "]"
        return " ::: ".join([name,
                #self.display_name,
                str(starting_points),
                str(points_for_solving),
                str(points_for_selling),
                str(expenditure),
                string_problems_solved,
                string_solutions_bought,
                string_solutions_sold
                ])


    @staticmethod
    def scoreFromTuple(string_tuple):
        _,start,solve,sell,expenses,_,_,_ = string_tuple
        return start + solve + sell - expenses

    def get_capital(self):
        return self.starting_points + self.points_for_solving + self.points_for_selling - self.expenditure

    def get_solved_problems(self):
        return self.problems_solved

    def solve_problem(self, problem, solution):
        result, points = problem.submit_solution(solution)
        if result and not problem in self.problems_solved:
            problem.times_solved += 1
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
            problem.times_solved += 1
            self.problems_solved.append(problem)
            self.points_for_solving += points
            self.expenditure += price
            return True
        else:
            return False

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

    def __str__(self):
        return ", ".join([self.problem.name, self.seller.name, str(self.price)])

    @staticmethod
    def fromString(string):
        parsed = string.split(", ")
        try:
            return (parsed[0], parsed[1], int(parsed[2]))
        except IndexError:
            return None

    @staticmethod
    def toString(info_tuple):
        return ", ".join([str(i) for i in info_tuple])

    def get_price(self):
        return self.price

    def set_price(self, new_price):
        self.price = new_price

    def purchase(self):
        return (self.problem.answer, self.problem)
