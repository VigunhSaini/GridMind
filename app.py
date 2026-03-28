"""
GridMind AI Backend — Flask REST API
=====================================
Endpoints:
  POST /predict-solar      → solar AC power prediction (kW, single plant)
  POST /predict-demand     → hourly energy demand prediction (MW)
  POST /optimize-energy    → combined prediction + unit-corrected smart decision

Run:
  python app.py
Server: http://localhost:5000
"""

import os
import numpy as np
import joblib
from flask import Flask, request, jsonify
from flask_cors import CORS

# ─────────────────────────────────────────────────────────
# App Setup
# ─────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)   # Allow frontend requests from different origin

# ─────────────────────────────────────────────────────────
# Load Models (once at startup)
# ─────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    solar_model  = joblib.load(os.path.join(BASE_DIR, "solar_model.pkl"))
    demand_model = joblib.load(os.path.join(BASE_DIR, "demand_model.pkl"))
    print("[OK] Models loaded successfully.")
except FileNotFoundError as e:
    print(f"[ERROR] Model file not found: {e}")
    print("  Run train_models.py first to generate solar_model.pkl & demand_model.pkl")
    solar_model = demand_model = None

# ─────────────────────────────────────────────────────────
# Scaling constant
# The solar model predicts a single plant/house output (kW).
# The demand model predicts regional grid-level load (MW).
# We multiply solar by DEFAULT_NUM_HOUSES so the comparison is meaningful.
# ─────────────────────────────────────────────────────────
DEFAULT_NUM_HOUSES = 100


# ─────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────
def models_ready():
    return solar_model is not None and demand_model is not None


# ─────────────────────────────────────────────────────────
# 1. /predict-solar
# ─────────────────────────────────────────────────────────
@app.route("/predict-solar", methods=["POST"])
def predict_solar():
    """
    Body: { "hour": int, "temperature": float, "irradiation": float }
    Returns: { "solar_prediction": float }   (kW — single plant)
    """
    if not models_ready():
        return jsonify({"error": "Models not loaded. Run train_models.py first."}), 503

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400

    required = ["hour", "temperature", "irradiation"]
    missing  = [k for k in required if k not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    try:
        features   = np.array([[float(data["hour"]), float(data["temperature"]), float(data["irradiation"])]])
        prediction = float(solar_model.predict(features)[0])
        return jsonify({"solar_prediction": round(prediction, 4)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────────────────
# 2. /predict-demand
# ─────────────────────────────────────────────────────────
@app.route("/predict-demand", methods=["POST"])
def predict_demand():
    """
    Body: { "hour", "temperature", "household_size", "ac_usage", "day_of_week", "is_weekend" }
    Returns: { "demand_prediction": float }   (kW)
    """
    if not models_ready():
        return jsonify({"error": "Models not loaded. Run train_models.py first."}), 503

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400

    required = ["hour", "temperature", "household_size", "ac_usage", "day_of_week", "is_weekend"]
    missing  = [k for k in required if k not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    try:
        features   = np.array([[float(data["hour"]), float(data["temperature"]),
                                 float(data["household_size"]), float(data["ac_usage"]),
                                 float(data["day_of_week"]), float(data["is_weekend"])]])
        prediction = float(demand_model.predict(features)[0])
        return jsonify({"demand_prediction": round(prediction, 4)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────────────────
# 3. /optimize-energy  (MAIN ENDPOINT)
# ─────────────────────────────────────────────────────────
@app.route("/optimize-energy", methods=["POST"])
def optimize_energy():
    if not models_ready():
        return jsonify({"error": "Models not loaded. Run train_models.py first."}), 503

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400

    # Removed lag features, added household features
    required = ["hour", "temperature", "irradiation",
                "household_size", "ac_usage", "day_of_week", "is_weekend"]
    missing  = [k for k in required if k not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    try:
        # ── Solar prediction — kW (single plant) ──────────
        solar_raw = float(solar_model.predict(np.array([[
            float(data["hour"]),
            float(data["temperature"]),
            float(data["irradiation"])
        ]]))[0])
        # Normalize solar (realistic range)
        solar_per_house = min(solar_raw, 10.0)

        # ── Demand prediction — per household kW ──────────
        demand_per_house = float(demand_model.predict(np.array([[
            float(data["hour"]),
            float(data["temperature"]),
            float(data["household_size"]),
            float(data["ac_usage"]),
            float(data["day_of_week"]),
            float(data["is_weekend"])
        ]]))[0])
        
        # ── Scale both to fleet level ──────────────────────
        num_houses     = int(data.get("num_houses", DEFAULT_NUM_HOUSES))
        solar_total = solar_per_house * num_houses
        demand_total = demand_per_house * num_houses
        
        # ── Surplus / Deficit (all kW) ────────────────────
        if solar_total > demand_total:
            surplus_kw = solar_total - demand_total
            deficit_kw = 0.0
            decision = "Share energy with neighbors"
            decision_type = "share"
        else:
            surplus_kw = 0.0
            deficit_kw = demand_total - solar_total
            decision = "Buy energy from grid"
            decision_type = "buy"

        return jsonify({
            "solar_per_house": round(solar_per_house,     2),
            "solar_total":     round(solar_total,         2),
            "demand_per_house":round(demand_per_house,    2),
            "demand_total":    round(demand_total,        2),
            "num_houses":      num_houses,
            "surplus_kw":      round(surplus_kw,          2),
            "deficit_kw":      round(deficit_kw,          2),
            "surplus_only":    round(surplus_kw,          2),
            "decision":        decision,
            "decision_type":   decision_type
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────────────────
# 4. /health
# ─────────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "models_loaded": models_ready()})


# ─────────────────────────────────────────────────────────
# Run
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
