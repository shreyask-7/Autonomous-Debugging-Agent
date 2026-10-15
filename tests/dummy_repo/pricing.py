def calculate_tax(subtotal: float) -> float:
    return subtotal * 0.10

def apply_discount(subtotal: float, discount_code: str) -> float:
    if discount_code == "SAVE20":
        return subtotal * 0.80
    return subtotal