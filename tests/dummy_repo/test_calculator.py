import unittest
from calculator import divide

class TestCalculator(unittest.TestCase):
    def test_divide_success(self):
        self.assertEqual(divide(10, 2), 5.0)

    def test_divide_zero(self):
        # We expect divide(10, 0) to return None or handle zero division gracefully,
        # but calculator.py currently raises ZeroDivisionError.
        self.assertIsNone(divide(10, 0))

if __name__ == "__main__":
    unittest.main()