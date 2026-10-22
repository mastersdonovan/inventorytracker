import os

from flask import Flask, jsonify, request
from flask_cors import CORS
from optimization import Optimization

app = Flask(__name__)
CORS(app, origins=[os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173")])

opt = Optimization.load_or_create()


def _parse_variable(data):
    """Return (name, unit_cost) from a request body, or None if invalid."""
    data = data or {}
    name = str(data.get("name", "")).strip()
    unit_cost = data.get("unit_cost")
    if not name or unit_cost is None:
        return None
    try:
        return name, float(unit_cost)
    except (TypeError, ValueError):
        return None


def _parse_week(data):
    """Return (units, margin) from a request body, or None if invalid."""
    data = data or {}
    units = data.get("units")
    margin = data.get("margin")
    if units is None or margin is None:
        return None
    try:
        return units, float(margin)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------

@app.route("/api/variables", methods=["GET"])
def get_variables():
    return jsonify(opt.get_variables())


@app.route("/api/variables", methods=["POST"])
def add_variable():
    parsed = _parse_variable(request.get_json(silent=True))
    if parsed is None:
        return jsonify({"error": "name and a numeric unit_cost are required"}), 400
    return jsonify(opt.add_variable(*parsed)), 201


@app.route("/api/variables/<int:index>", methods=["PUT"])
def update_variable(index):
    parsed = _parse_variable(request.get_json(silent=True))
    if parsed is None:
        return jsonify({"error": "name and a numeric unit_cost are required"}), 400
    try:
        return jsonify(opt.update_variable(index, *parsed))
    except IndexError:
        return jsonify({"error": "Index out of range"}), 404


@app.route("/api/variables/<int:index>", methods=["DELETE"])
def remove_variable(index):
    try:
        return jsonify(opt.remove_variable(index))
    except IndexError:
        return jsonify({"error": "Index out of range"}), 404


# ---------------------------------------------------------------------------
# Weeks
# ---------------------------------------------------------------------------

@app.route("/api/weeks", methods=["GET"])
def get_weeks():
    return jsonify(opt.get_weeks())


@app.route("/api/weeks", methods=["POST"])
def add_week():
    parsed = _parse_week(request.get_json(silent=True))
    if parsed is None:
        return jsonify({"error": "units and a numeric margin are required"}), 400
    try:
        opt.add_week(*parsed)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"ok": True}), 201


@app.route("/api/weeks/<int:index>", methods=["PUT"])
def update_week(index):
    parsed = _parse_week(request.get_json(silent=True))
    if parsed is None:
        return jsonify({"error": "units and a numeric margin are required"}), 400
    try:
        opt.update_week(index, *parsed)
    except IndexError:
        return jsonify({"error": "Index out of range"}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"ok": True})


@app.route("/api/weeks/<int:index>", methods=["DELETE"])
def remove_week(index):
    try:
        opt.remove_week(index)
    except IndexError:
        return jsonify({"error": "Index out of range"}), 404
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

@app.route("/api/results", methods=["GET"])
def get_results():
    variables = opt.get_variables()
    if len(variables) == 0:
        return jsonify({"error": "No variables defined"}), 400

    try:
        optimal_weekly = opt.get_weighted_average()
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    results = []
    for v, weekly in zip(variables, optimal_weekly):
        results.append({
            "name": v["name"],
            "unit_cost": v["unit_cost"],
            "daily":   round(weekly / 7,        1),
            "weekly":  round(weekly,             1),
            "monthly": round(weekly * (52 / 12), 1),
        })

    return jsonify({"variables": results})


if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_mode, port=5000)