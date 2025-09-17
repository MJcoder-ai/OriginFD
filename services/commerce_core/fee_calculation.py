class FeeCalculator:
    """Basic fee and carbon calculation engine."""

    def __init__(
        self,
        cost_per_psu: float = 0.01,
        carbon_per_psu: float = 0.005,
        savings_rate: float = 0.002,
    ) -> None:
        self.cost_per_psu = cost_per_psu
        self.carbon_per_psu = carbon_per_psu
        self.savings_rate = savings_rate

    def calculate_fee(self, psu: int) -> dict:
        fee = psu * self.cost_per_psu
        savings = psu * self.savings_rate
        carbon = psu * self.carbon_per_psu
        return {
            "fee": fee,
            "savings": savings,
            "carbon": carbon,
        }
