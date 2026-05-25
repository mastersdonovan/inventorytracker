import optimization

class Inventory:
    def __init__(self, document_id="main"):
        self.document_id = document_id
        try:
            self.optimization = optimization.Optimization.load(self.document_id)
        except FileNotFoundError:
            self.optimization = optimization.Optimization([[0, 0, 0]], [0], document_id=self.document_id)

    def add_week(self, week_data, margin):
        self.optimization.add_week(week_data, margin)

    def add_input(self):
        variables = self.optimization.variables
        if not variables:
            print("No variables defined. Add variables first.")
            return
        values = []
        for v in variables:
            while True:
                try:
                    values.append(float(input(f"  {v['name']} (units): ")))
                    break
                except ValueError:
                    print("  Invalid input — please enter a number.")
        while True:
            try:
                margin = float(input("  Margin ($): "))
                break
            except ValueError:
                print("  Invalid input — please enter a number.")
        self.add_week(values, margin)

    def update_previous_week(self, week_index, week_data, margin):
        self.optimization.update_previous_week(week_index, week_data, margin)

    def remove_week(self, week_index):
        self.optimization.remove_week(week_index)

    def get_optimal_x(self):
        return self.optimization.get_optimal_x()
