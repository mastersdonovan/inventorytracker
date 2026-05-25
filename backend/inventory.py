import optimization
import numpy as np

class Inventory:
    def __init__(self, document_id="main"):
        self.document_id = document_id
        try:
            self.optimization = optimization.Optimization.load(self.document_id)
        except FileNotFoundError:
            self.optimization = optimization.Optimization([[0, 0, 0]], [0], self.document_id)
        self.product = {
            "cur_amt": self.optimization.A.to_numpy().tolist(),
            "amt-used": self.optimization.b.tolist(),
        }

    def add_week(self, week_data):
        self.optimization.add_week(week_data)

    def add_input(self):
        """Prompt the user to enter this week's data interactively."""
        fields = [
            ("Units purchased", int),
            ("Unit cost",       float),
            ("Current stock",   int),
            ("Units sold",      int),
        ]
        # Loop until valid input is received for each field, add the weeks data to the optimization model
        values = []
        for label, cast in fields:
            while True:
                try:
                    values.append(cast(input(f"  {label}: ")))
                    break
                except ValueError:
                    print(f"  Invalid input — please enter a {'whole number' if cast is int else 'number'}.")
        self.add_week(values)
    def update_previous_week(self, week_index, week_data):
        self.optimization.update_previous_week(week_index, week_data)

    def remove_week(self, week_index):
        self.optimization.remove_week(week_index)
    
    def get_optimal_x(self):
        return self.optimization.get_optimal_x()

    def optimal_purchase(self, unit_cost, current_stock):
        """Return the units to purchase so stock exactly covers predicted demand."""
        x = self.get_optimal_x()
        x0, x1, x2 = x[0], x[1], x[2]
        if (1 - x0) == 0:
            raise ValueError("Model coefficient x0 == 1; cannot solve for optimal purchase.")
        P = (x1 * unit_cost + (x2 - 1) * current_stock) / (1 - x0)
        return max(0.0, P)

    def get_margin(self, unit_cost, current_stock, selling_price):
        """Return optimal purchase, units remaining, and dollar profit."""
        x = self.get_optimal_x()
        x0, x1, x2 = x[0], x[1], x[2]
        P = self.optimal_purchase(unit_cost, current_stock)
        predicted_demand = x0 * P + x1 * unit_cost + x2 * current_stock
        units_remaining = current_stock + P - predicted_demand
        dollar_profit = predicted_demand * selling_price - P * unit_cost
        return {
            "optimal_purchase": P,
            "units_remaining": units_remaining,
            "dollar_profit": dollar_profit,
        }
