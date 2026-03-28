"""
GridMind AI Engine — Model Training Script
==========================================
Models trained:+
  1. Solar energy output  → RandomForestRegressor  (AC_POWER)
  2. Energy demand        → XGBRegressor            (AEP_MW)

Datasets expected (relative to this script):
  SolarPower/Plant_1_Generation_Data.csv
  SolarPower/Plant_1_Weather_Sensor_Data.csv
  HourlyEnergy/AEP_hourly.csv

Outputs:
  solar_model.pkl
  demand_model.pkl
"""

import os
import sys
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import joblib

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from xgboost import XGBRegressor

# ─────────────────────────────────────────────────────────
# 0. Paths  (everything lives next to this script)
# ─────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SOLAR_GEN_CSV     = os.path.join(BASE_DIR, "SolarPower", "Plant_1_Generation_Data.csv")
SOLAR_WEATHER_CSV = os.path.join(BASE_DIR, "SolarPower", "Plant_1_Weather_Sensor_Data.csv")
ENERGY_CSV        = os.path.join(BASE_DIR, "HourlyEnergy", "household_energy_consumption.csv")

SOLAR_MODEL_PATH  = os.path.join(BASE_DIR, "solar_model.pkl")
DEMAND_MODEL_PATH = os.path.join(BASE_DIR, "demand_model.pkl")


# ─────────────────────────────────────────────────────────
# 1. Helpers
# ─────────────────────────────────────────────────────────
def check_files(*paths):
    """Verify that all required CSV files exist before training."""
    for p in paths:
        if not os.path.isfile(p):
            print(f"[ERROR] File not found: {p}")
            sys.exit(1)
    print("[OK] All dataset files found.\n")


def section(title: str):
    print("\n" + "═" * 55)
    print(f"  {title}")
    print("═" * 55)


# ─────────────────────────────────────────────────────────
# 2. Load & Preprocess — Solar Data
# ─────────────────────────────────────────────────────────
def load_solar_data():
    section("SOLAR DATA — Loading & Preprocessing")

    # Load generation data (contains AC_POWER target)
    gen = pd.read_csv(SOLAR_GEN_CSV)
    print(f"  Generation data shape  : {gen.shape}")

    # Load weather sensor data (contains temperature & irradiation)
    weather = pd.read_csv(SOLAR_WEATHER_CSV)
    print(f"  Weather sensor shape   : {weather.shape}")

    # Parse timestamps for both files
    gen["DATE_TIME"]     = pd.to_datetime(gen["DATE_TIME"],    dayfirst=True, errors="coerce")
    weather["DATE_TIME"] = pd.to_datetime(weather["DATE_TIME"], errors="coerce")

    # Keep only the columns we need before merging
    gen     = gen[["DATE_TIME", "PLANT_ID", "AC_POWER"]].copy()
    weather = weather[["DATE_TIME", "PLANT_ID", "AMBIENT_TEMPERATURE", "IRRADIATION"]].copy()

    # Merge on timestamp + plant so each generation row gets its weather reading
    solar = pd.merge(gen, weather, on=["DATE_TIME", "PLANT_ID"], how="inner")
    print(f"  Merged solar shape     : {solar.shape}")

    # Extract hour feature
    solar["hour"] = solar["DATE_TIME"].dt.hour

    # Select model features & target
    feature_cols = ["hour", "AMBIENT_TEMPERATURE", "IRRADIATION"]
    target_col   = "AC_POWER"

    # Ensure numeric & drop NaNs
    solar[feature_cols + [target_col]] = solar[feature_cols + [target_col]].apply(
        pd.to_numeric, errors="coerce"
    )
    solar.dropna(subset=feature_cols + [target_col], inplace=True)

    print(f"  Clean solar shape      : {solar.shape}")
    print(f"  Features               : {feature_cols}")
    print(f"  Target                 : {target_col}")

    X = solar[feature_cols].values
    y = solar[target_col].values
    return X, y, feature_cols, target_col


# ─────────────────────────────────────────────────────────
# 3. Load & Preprocess — Energy Demand Data  (XGBoost-ready)
# ─────────────────────────────────────────────────────────
def load_energy_data():
    section("HOUSEHOLD DEMAND DATA — Loading & Preprocessing")
    
    ENERGY_CSV = os.path.join(BASE_DIR, "HourlyEnergy", "household_energy_consumption.csv")
    energy = pd.read_csv(ENERGY_CSV)
    
    # Preprocessing
    energy['Datetime'] = pd.to_datetime(energy['Date'])
    energy['hour'] = energy['Datetime'].dt.hour
    energy['day_of_week'] = energy['Datetime'].dt.dayofweek
    energy['is_weekend'] = energy['day_of_week'].isin([5, 6]).astype(int)
    
    # Map AC
    energy['ac_usage'] = energy['Has_AC'].map({'Yes': 1, 'No': 0}).fillna(0).astype(int)
    energy['temperature'] = energy['Avg_Temperature_C']
    energy['household_size'] = energy['Household_Size']
    energy['energy_consumption'] = energy['Energy_Consumption_kWh']
    
    feature_cols = [
        'hour',
        'temperature',
        'household_size',
        'ac_usage',
        'day_of_week',
        'is_weekend'
    ]
    target_col = 'energy_consumption'
    
    energy.dropna(subset=feature_cols + [target_col], inplace=True)
    energy.reset_index(drop=True, inplace=True)
    
    print(f"  Clean energy shape : {energy.shape}")
    print(f"  Features           : {feature_cols}")
    print(f"  Target             : {target_col}")
    
    return energy, feature_cols, [], target_col


# ─────────────────────────────────────────────────────────
# 4a. Train & Evaluate — Solar  (RandomForest, random split)
# ─────────────────────────────────────────────────────────
def train_and_evaluate(X, y, label: str, n_estimators: int = 100, random_state: int = 42):
    """
    Splits data randomly 80/20, trains a RandomForestRegressor,
    evaluates and returns the trained model + test arrays for plotting.
    Used for the Solar model only.
    """
    section(f"TRAINING — {label}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state
    )
    print(f"  Train samples : {len(X_train)}")
    print(f"  Test  samples : {len(X_test)}")

    model = RandomForestRegressor(
        n_estimators=n_estimators,
        n_jobs=-1,           # use all CPU cores
        random_state=random_state
    )
    model.fit(X_train, y_train)
    print(f"  Training complete ✓")

    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    r2  = r2_score(y_test, y_pred)

    print(f"\n  ── Evaluation Results ──────────────────────")
    print(f"  MAE  : {mae:,.4f}")
    print(f"  R²   : {r2:.4f}")
    print(f"  ────────────────────────────────────────────")

    return model, y_test, y_pred


# ─────────────────────────────────────────────────────────
# 4b. Train & Evaluate — Demand  (XGBoost, 70-20-10 split)
# ─────────────────────────────────────────────────────────
def train_demand_model(energy_df, feature_cols, baseline_cols, target_col,
                       n_estimators: int = 200):
    section("TRAINING — Household Demand Model (XGBoost)")

    X = energy_df[feature_cols].values
    y = energy_df[target_col].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    demand_model = XGBRegressor(
        n_estimators=n_estimators,
        learning_rate=0.05,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42
    )
    print("\\n===== HOUSEHOLD DEMAND MODEL =====")
    for i in range(n_estimators):
        demand_model.n_estimators = i + 1
        demand_model.fit(X_train, y_train, verbose=False)
        if (i+1) % 20 == 0 or i == n_estimators - 1:
            progress = ((i + 1) / n_estimators) * 100
            print(f"Training Progress: {progress:.2f}%")

    y_pred = demand_model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print(f"MAE: {mae:.2f} kW")
    print(f"R²: {r2:.4f} ({r2*100:.2f}%)")

    return demand_model, y_test, y_pred


# ─────────────────────────────────────────────────────────
# 5. Save Models
# ─────────────────────────────────────────────────────────
def save_model(model, path: str, label: str):
    joblib.dump(model, path)
    print(f"\n  [{label}] Model saved → {path}")


# ─────────────────────────────────────────────────────────
# 6. Visualisation — Actual vs Predicted
# ─────────────────────────────────────────────────────────
def plot_results(y_test_solar, y_pred_solar, y_test_energy, y_pred_energy):
    section("VISUALISATION — Actual vs Predicted")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("GridMind — Model Predictions vs Actuals", fontsize=14, fontweight="bold")

    # Sample at most 500 points so the scatter is readable
    MAX_POINTS = 500

    def _scatter(ax, y_true, y_pred, title, unit):
        n   = min(len(y_true), MAX_POINTS)
        idx = np.random.choice(len(y_true), n, replace=False)
        ax.scatter(y_true[idx], y_pred[idx], alpha=0.4, edgecolors="none", s=20, color="#4F8EF7")
        lims = [min(y_true.min(), y_pred.min()), max(y_true.max(), y_pred.max())]
        ax.plot(lims, lims, "r--", linewidth=1.2, label="Perfect prediction")
        ax.set_xlabel(f"Actual ({unit})")
        ax.set_ylabel(f"Predicted ({unit})")
        ax.set_title(title)
        ax.legend(fontsize=8)

    _scatter(axes[0], y_test_solar,  y_pred_solar,  "Solar Output Prediction",  "kW")
    _scatter(axes[1], y_test_energy, y_pred_energy, "Energy Demand Prediction", "MW")

    plt.tight_layout()
    plot_path = os.path.join(BASE_DIR, "model_predictions.png")
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    print(f"  Plot saved → {plot_path}")
    plt.show()


# ─────────────────────────────────────────────────────────
# 7. Prediction Functions  (importable by other modules)
# ─────────────────────────────────────────────────────────

# These are populated after training so this module can be imported directly.
_solar_model  = None
_demand_model = None


def predict_solar(hour: float, temperature: float, irradiation: float) -> float:
    """
    Predict solar AC power output.

    Parameters
    ----------
    hour        : int/float  Hour of day (0–23)
    temperature : float      Ambient temperature in °C
    irradiation : float      Solar irradiation (W/m²)

    Returns
    -------
    float  Predicted AC power in kW
    """
    if _solar_model is None:
        raise RuntimeError("Solar model not loaded. Run train_models.py first.")
    return float(_solar_model.predict([[hour, temperature, irradiation]])[0])


def predict_demand(hour: float, temperature: float, household_size: float, 
                   ac_usage: float, day_of_week: float, is_weekend: float) -> float:
    """Predict household electricity demand in kW."""
    if _demand_model is None:
        raise RuntimeError("Demand model not loaded. Run train_models.py first.")
    features = [[hour, temperature, household_size, ac_usage, day_of_week, is_weekend]]
    return float(_demand_model.predict(features)[0])


def load_saved_models():
    """
    Load persisted .pkl models into module-level variables so the
    predict_* functions work without re-training.

    Usage (from another module):
        from train_models import load_saved_models, predict_solar, predict_demand
        load_saved_models()
        print(predict_solar(12, 30, 0.8))
    """
    global _solar_model, _demand_model
    _solar_model  = joblib.load(SOLAR_MODEL_PATH)
    _demand_model = joblib.load(DEMAND_MODEL_PATH)
    print("[OK] Models loaded from disk.")


# ─────────────────────────────────────────────────────────
# 8. Main
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Verify datasets exist
    check_files(SOLAR_GEN_CSV, SOLAR_WEATHER_CSV, ENERGY_CSV)

    # ── Solar ──
    X_solar, y_solar, solar_features, solar_target = load_solar_data()
    solar_model, y_test_solar, y_pred_solar = train_and_evaluate(
        X_solar, y_solar, label="Solar Energy Output"
    )
    save_model(solar_model, SOLAR_MODEL_PATH, "Solar")

    # ── Energy Demand (XGBoost) ──
    energy_df, energy_features, baseline_features, energy_target = load_energy_data()
    demand_model, y_test_energy, y_pred_energy = train_demand_model(
        energy_df, energy_features, baseline_features, energy_target,
        n_estimators=200
    )
    save_model(demand_model, DEMAND_MODEL_PATH, "Demand")

    # ── Make module-level models available (in case this is imported) ──
    _solar_model  = solar_model
    _demand_model = demand_model

    # ── Quick sanity-check predictions ──
    # Use representative typical values for the demand features
    section("SAMPLE PREDICTIONS")
    print(f"  predict_solar(hour=12, temp=28, irradiation=0.75) "
          f"→ {predict_solar(12, 28, 0.75):,.2f} kW")
    print(f"  predict_demand(hour=18, temp=22, size=4, ac=1, day=1, weekend=0)")
    print(f"  → {predict_demand(18, 22, 4, 1, 1, 0):,.2f} kW")

    # ── Visualisation ──
    plot_results(y_test_solar, y_pred_solar, y_test_energy, y_pred_energy)

    section("DONE")
    print("  Models trained and saved successfully.")
    print(f"  solar_model.pkl  → {SOLAR_MODEL_PATH}")
    print(f"  demand_model.pkl → {DEMAND_MODEL_PATH}\n")
