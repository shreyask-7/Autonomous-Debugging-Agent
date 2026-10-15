import unittest
from cart import ShoppingCart

class TestShoppingCart(unittest.TestCase):
    def test_checkout_no_discount(self):
        cart = ShoppingCart()
        cart.add_item(100.0)
        self.assertEqual(cart.checkout(), 110.0)

    def test_checkout_with_discount(self):
        cart = ShoppingCart()
        cart.add_item(100.0)
        # 100 * 0.80 = 80. Tax on 80 = 8. Total should be 88.0.
        # Currently, it calculates tax on 100 (10.0), returning 90.0.
        self.assertEqual(cart.checkout(discount_code="SAVE20"), 88.0)

if __name__ == '__main__':
    unittest.main()