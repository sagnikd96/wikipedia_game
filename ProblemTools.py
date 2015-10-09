from itertools import takewhile
from UserTools import decomment
from logic import Problem

PROBLEM_FILE = "problem_file.dat"

def parseProblemFile(filename, comment="#"):
    problems = {}
    for line in decomment(filename, comment):
        name, display_name, answer, base_points, multiplier, *dependencies = line.strip().split(", ")
        problems[name] = str(Problem(name, display_name, answer, int(base_points), float(multiplier), dependencies))
    return problems
