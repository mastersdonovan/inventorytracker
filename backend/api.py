import numpy as np
from flask import Flask, jsonify, request
from flask_cors import CORS
from inventory import Inventory
from optimization import Matrix

app = Flask(__name__)
CORS(app)

inv = Inventory()


# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------

@app.route("/api/variables", methods=["GET"])
def get_variables():
    return jsonify(inv.optimization.variables)


@app.route("/api/variables", methods=["POST"])
def add_variable():
    data = request.get_json()
    name = data.get("name", "").strip()
    unit_cost = data.get("unit_cost")
    if not name or unit_cost is None:
        return jsonify({"error": "name and unit_cost are required"}), 400
    if len(inv.optimization.variables) == 0:
        # Clear the placeholder row so real week data starts fresh
        inv.optimization.A = Matrix(np.zeros((0, 0)))
        inv.optimization.b = np.zeros(0)
    inv.optimization.variables.append({"name": name, "unit_cost": float(unit_cost)})
    inv.optimization.A.add_column()
    inv.optimization._save()
    return jsonify(inv.optimization.variables), 201


@app.route("/api/variables/<int:index>", methods=["DELETE"])
def remove_variable(index):
    variables = inv.optimization.variables
    if index < 0 or index >= len(variables):
        return jsonify({"error": "Index out of range"}), 404
    inv.optimization.variables.pop(index)
    inv.optimization.A.remove_column(index)
    inv.optimization._save()
    return jsonify(inv.optimization.variables)


# ---------------------------------------------------------------------------
# Weeks
# ---------------------------------------------------------------------------

@app.route("/api/weeks", methods=["GET"])
def get_weeks():
    if not inv.optimization.variables:
        return jsonify([])
    A = inv.optimization.A.to_numpy().tolist()
    b = inv.optimization.b.tolist()
    weeks = [{"units": row, "margin": margin} for row, margin in zip(A, b)]
    return jsonify(weeks)


@app.route("/api/weeks", methods=["POST"])
def add_week():
    data = request.get_json()
    units = data.get("units")
    margin = data.get("margin")
    if units is None or margin is None:
        return jsonify({"error": "units and margin are required"}), 400
    try:
        inv.add_week(units, float(margin))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"ok": True}), 201


@app.route("/api/weeks/<int:index>", methods=["PUT"])
def update_week(index):
    data = request.get_json()
    units = data.get("units")
    margin = data.get("margin")
    if units is None or margin is None:
        return jsonify({"error": "units and margin are required"}), 400
    try:
        inv.optimization.update_previous_week(index, units, float(margin))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"ok": True})


@app.route("/api/weeks/<int:index>", methods=["DELETE"])
def remove_week(index):
    inv.remove_week(index)
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

@app.route("/api/results", methods=["GET"])
def get_results():
    variables = inv.optimization.variables
    if len(variables) == 0:
        return jsonify({"error": "No variables defined"}), 400
    unit_costs = [v["unit_cost"] for v in variables]
    x = inv.get_optimal_x().tolist()
    results = [
        {
            "name": v["name"],
            "unit_cost": v["unit_cost"],
            "optimal_purchase": round(max(0.0, coef), 2),
        }
        for v, coef in zip(variables, x)
    ]
    return jsonify({"variables": results, "coefficients": x})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
