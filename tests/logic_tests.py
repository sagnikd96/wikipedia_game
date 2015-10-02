import sys
import unittest

sys.path.insert(0, '../')

import logic as lg

class ProblemTests(unittest.TestCase):

    def test1(self):
        a = lg.Problem("prob1", "A", 1, 10000, 0.75)
        expected = (False, 0)
        result = a.submit_solution(5)
        self.assertTrue(expected == result)

    def test2(self):
        a = lg.Problem("prob2", "A", 1, 400, 0.5)
        expected1 = (True, 400)
        expected2 = (True, 200)
        expected3 = (True, 100)
        self.assertTrue(expected1 == a.submit_solution(1))
        self.assertTrue(expected2 == a.submit_solution(1))
        self.assertTrue(expected3 == a.submit_solution(1))

    def test3(self):
        a = lg.Problem("prob3", "A", 1, 3.1, 0.5)
        expected = (True, 2)
        a.submit_solution(1)
        self.assertTrue(expected == a.submit_solution(1))

    def test4(self):
        a = lg.Problem("prob3", "Problem 3", "1", 10, 0.5)
        result1 = "prob3, Problem 3, 1, 10, 0.5, 1, 10"
        self.assertTrue(str(a) == result1)
        self.assertTrue(lg.Problem.fromString(result1) == a)
        a.submit_solution("1")
        result2 = "prob3, Problem 3, 1, 10, 0.5, 2, 5"
        self.assertTrue(str(a) == result2)
        self.assertTrue(lg.Problem.fromString(result2) == a)

    def test5(self):
        a = lg.Problem("prob3", "Problem 3", "1", 10, 0.5)
        b = lg.Problem("prob3", "Problem 3", "1", 10, 0.5)
        c = lg.Problem("prob4", "Problem 3", "1", 10, 0.5)
        self.assertTrue(a==b)
        self.assertTrue(a!=c)

    def test6(self):
        a = lg.Problem("prob3", "Problem 3", "1", 10, 0.5)
        self.assertTrue(lg.Problem.fromString(str(a)) == a)

class UserLogicTests(unittest.TestCase):

    def test1(self):
        a = lg.UserLogic("a", 100)
        self.assertTrue(a.get_capital() == 100)
        a.points_for_solving = 30
        self.assertTrue(a.get_capital() == 130)
        a.points_for_selling = 40
        self.assertTrue(a.get_capital() == 170)
        a.expenditure = 80
        self.assertTrue(a.get_capital() == 90)

    def test2(self):
        a = lg.UserLogic("a", 100)
        b = lg.Problem("prob1", "A", 1, 40, 0.5)
        self.assertTrue(a.solve_problem(b, 2) == False)
        self.assertTrue(a.get_capital() == 100)
        self.assertTrue(a.solve_problem(b, 1) == True)
        self.assertTrue(a.get_capital() == 140)
        self.assertTrue(a.solve_problem(b, 1) == False)
        self.assertTrue(a.get_capital() == 140)

    def test3(self):
        a = lg.Problem("a", "A", 1, 40, 0.5)
        b = lg.UserLogic("a", 100)
        expected = [lg.Commodity(a, b, 120)]
        self.assertTrue(b.sell_problem(a, 120) == False)
        b.solve_problem(a, 1)
        self.assertTrue(b.sell_problem(a, 120) == True)
        self.assertTrue(b.get_capital() == 100 + 40 - lg.MARKET_FEE_NEW_ITEM)
        self.assertTrue(b.solutions_sold == expected)
        self.assertTrue(b.sell_problem(a, 120) == False)
        self.assertTrue(b.get_capital() == 100 + 40 - lg.MARKET_FEE_NEW_ITEM)

    def test4(self):
        a = lg.Problem("a", "A", 1, 40, 0.5)
        b = lg.UserLogic("a", 100)
        c = lg.Commodity(a, b, 120)
        self.assertTrue(b.change_price(c, 100) == False)
        b.solutions_sold = [c]
        self.assertTrue(b.change_price(c, 100) == True)
        self.assertTrue(b.get_capital() == 100 - lg.MARKET_FEE_CHANGE_PRICE)
        b.expenditure = 99
        self.assertTrue(b.change_price(c, 100) == False)

    def test5(self):
        a = lg.Problem("a", "A", 1, 40, 0.5)
        b1 = lg.UserLogic("a", 100)
        b2 = lg.UserLogic("b", 70)
        self.assertTrue(b1.sell_problem(a, 80) == False)
        b1.solve_problem(a, 1)
        self.assertTrue(b1.get_capital() == 140)
        self.assertTrue(b1.sell_problem(a, 80) == True)
        self.assertTrue(b1.get_capital() == 140 - lg.MARKET_FEE_NEW_ITEM)
        self.assertTrue(b2.buy_solution(b1.solutions_sold[0]) == False)
        b2.starting_points = 100
        self.assertTrue(b2.buy_solution(b1.solutions_sold[0]) == True)
        self.assertTrue(b2.get_capital() == 100 - 80 + 20)

#    def test6(self):
#        a = lg.Problem("a", "A", 1, 40, 0.5)
#        b = lg.Problem("a", "A", 1, 40, 0.5)
#        c = lg.Problem("b", "A", 1, 40, 0.5)
#        self.assertTrue(a==b)
#        self.assertTrue(a!=c)

    def test7(self):
        a1 = lg.Problem("a", "A", 1, 40, 0.5)
        a2 = lg.Problem("b", "A", 1, 40, 0.5)
        a3 = lg.Problem("c", "A", 1, 40, 0.5)
        a4 = lg.Problem("d", "A", 1, 40, 0.5)
        b1 = lg.UserLogic("user1", 100)
        c1 = lg.Commodity(a1, b1, 120)
        c2 = lg.Commodity(a2, b1, 120)
        b1.problems_solved = [a1, a2, a3, a4]
        b1.solutions_bought = [a3, a4]
        b1.solutions_sold = [c1, c2]
        result = "user1 ::: 100 ::: 0 ::: 0 ::: 0 ::: ['a', 'b', 'c', 'd'] ::: ['c', 'd'] ::: [a, user1, 120 :: b, user1, 120]"
        self.assertTrue(str(b1) == result)

    def test8(self):
        a = "user1 ::: 100 ::: 0 ::: 0 ::: 0 ::: ['a', 'b', 'c', 'd'] ::: ['c', 'd'] ::: [a, user1, 120 :: b, user1, 120]"
        result = ["user1", 100, 0, 0, 0, ["a", "b", "c", "d"], ["c", "d"], [("a", "user1", 120), ("b", "user1", 120)]]
        self.assertTrue(lg.UserLogic.fromString(a) == result)

    def test9(self):
        a1 = lg.Problem("a", "A", 1, 40, 0.5)
        a2 = lg.Problem("b", "A", 1, 40, 0.5)
        a3 = lg.Problem("c", "A", 1, 40, 0.5)
        a4 = lg.Problem("d", "A", 1, 40, 0.5)
        b1 = lg.UserLogic("user1", 100)
        b2 = lg.UserLogic("user2", 100)
        c1 = lg.Commodity(a1, b1, 120)
        c2 = lg.Commodity(a2, b1, 120)
        b1.problems_solved = [a1, a2, a3, a4]
        b1.solutions_bought = [a3, a4]
        b1.solutions_sold = [c1, c2]
        expected1 = ["user1", 100, 0, 0, 0, ["a", "b", "c", "d"], ["c", "d"], [("a", "user1", 120), ("b", "user1", 120)]]
        expected2 = ["user2", 100, 0, 0, 0, [], [], []]
        self.assertTrue(lg.UserLogic.fromString(str(b1)) == expected1)
        self.assertTrue(lg.UserLogic.fromString(str(b2)) == expected2)


class CommodityTests(unittest.TestCase):

    def test1(self):
        a1 = lg.Problem("a", "A", 1, 40, 0.5)
        a2 = lg.Problem("a", "A", 2, 40, 0.5)
        a3 = lg.Problem("b", "A", 1, 40, 0.5)
        b1 = lg.UserLogic("a", 100)
        b2 = lg.UserLogic("a", 100)
        b3 = lg.UserLogic("b", 100)
        c1 = lg.Commodity(a1, b1, 120)
        c2 = lg.Commodity(a1, b2, 120)
        c3 = lg.Commodity(a1, b3, 120)
        c4 = lg.Commodity(a2, b1, 120)
        c5 = lg.Commodity(a2, b2, 120)
        c6 = lg.Commodity(a2, b3, 120)
        c7 = lg.Commodity(a3, b1, 120)
        c8 = lg.Commodity(a3, b2, 120)
        c9 = lg.Commodity(a3, b3, 120)
        self.assertTrue(c1 != c3)
        self.assertTrue(c1 == c2)
        self.assertTrue(c2 == c4)

    def test2(self):
        a = lg.Problem("a", "A", 1, 40, 0.5)
        b = lg.UserLogic("a", 100)
        c = lg.Commodity(a, b, 120)
        self.assertTrue(c.get_price() == 120)
        c.set_price(110)
        self.assertTrue(c.get_price() == 110)
        self.assertTrue(c.purchase() == (1, a))

    def test3(self):
        a = lg.Problem("a", "A", 1, 40, 0.5)
        b = lg.UserLogic("a", 100)
        c = lg.Commodity(a, b, 120)
        result = "a, a, 120"
        self.assertTrue(str(c) == result)

    def test4(self):
        a = lg.Problem("a", "A", 1, 40, 0.5)
        b = lg.UserLogic("a", 100)
        c = "c, c, 10"
        result = ("c", "c", 10)
        self.assertTrue(lg.Commodity.fromString(c) == result)

    def test5(self):
        a = lg.Problem("a", "A", 1, 40, 0.5)
        b = lg.UserLogic("b", 100)
        c = lg.Commodity(a, b, 120)
        expected = ("a", "b", 120)
        self.assertTrue(lg.Commodity.fromString(str(c)) == expected)

def main():
    unittest.main()

if __name__=="__main__":
    main()
