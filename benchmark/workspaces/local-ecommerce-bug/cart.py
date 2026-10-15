from pricing import calculate_tax, apply_discount

class ShoppingCart:
    def __init__(self):
        self.items = []

    def add_item(self, price: float):
        self.items.append(price)

    def checkout(self, discount_code: str = None) -> float:
        subtotal = sum(self.items)
        discounted_total = apply_discount(subtotal, discount_code) if discount_code else subtotal
        tax = calculate_tax(discounted_total)
        
        return discounted_total + tax
