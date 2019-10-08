import unittest


class TestMultiIndexColumnRename(unittest.TestCase):
    def test_upper(self):
        name = "robbie"
        self.assertEqual("ROBBIE", name.upper())


if __name__ == "__main__":
    unittest.main()
