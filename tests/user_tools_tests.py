import sys
import unittest

sys.path.insert(0, '../')

import UserTools as ut

class UserTests(unittest.TestCase):

    def test1(self):
        self.assertTrue(ut.User.get("tappu") == "tappu")
        self.assertTrue(ut.User.get("khan") == "khan")
        self.assertTrue(ut.User.get("test1") == None)

def main():
    unittest.main()

if __name__=="__main__":
    main()
