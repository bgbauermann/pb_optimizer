from dataclasses import dataclass

@dataclass
class Trade:
    side: str
    security_id: int
    quantity: float
    price: float
    accrued_interest: float

    def get_market_value(self):
        return self.quantity * (self.price + self.accrued_interest)
