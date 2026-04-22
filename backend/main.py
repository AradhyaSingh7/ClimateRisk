# ============================================================
# CLIMATERISK — PHASE 3: FastAPI Backend
# ============================================================
# Setup:
#   pip install fastapi uvicorn joblib xgboost scikit-learn pandas numpy
#   Place your trained model .pkl files in ./models/
#   Run: uvicorn main:app --reload --port 8000
# ============================================================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
import joblib
import json
import numpy as np
import pandas as pd
import os

app = FastAPI(
    title="ClimateRisk API",
    description="Climate disaster risk scoring and financial exposure prediction",
    version="1.0.0"
)

# Allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Load models on startup ────────────────────────────────────
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")

def load_models():
    models = {}
    try:
        models["classifier"]  = joblib.load(f"{MODELS_DIR}/risk_classifier.pkl")
        models["regressor"]   = joblib.load(f"{MODELS_DIR}/damage_regressor.pkl")
        models["forecaster"]  = joblib.load(f"{MODELS_DIR}/risk_forecaster.pkl")
        models["le_state"]    = joblib.load(f"{MODELS_DIR}/le_state.pkl")
        models["le_category"] = joblib.load(f"{MODELS_DIR}/le_category.pkl")

        with open(f"{MODELS_DIR}/model_meta.json") as f:
            models["meta"] = json.load(f)

        print("✓ All models loaded")
    except Exception as e:
        print(f"⚠ Model loading failed: {e}")
        print("  API will return mock data until real models are placed in ./models/")
        models["meta"] = {"features": [], "shap_top_features": []}
    return models

MODELS = load_models()

# ── Pydantic schemas ──────────────────────────────────────────
class RiskRequest(BaseModel):
    state: str = Field(..., example="TX")
    disaster_category: str = Field(..., example="flood")
    year: int = Field(default=2024, ge=2000, le=2030)
    event_count: float = Field(default=10.0, ge=0)
    mean_damage: float = Field(default=500000.0, ge=0)
    rolling_5yr_events: float = Field(default=8.0, ge=0)
    rolling_5yr_damage: float = Field(default=400000.0, ge=0)
    damage_yoy: float = Field(default=0.05)
    total_deaths: float = Field(default=0.0, ge=0)
    total_injuries: float = Field(default=0.0, ge=0)
    mean_lat: float = Field(default=31.0)
    mean_lon: float = Field(default=-97.0)

class RiskResponse(BaseModel):
    state: str
    disaster_category: str
    year: int
    risk_score: float           # 0–100
    risk_tier: str              # Low / Medium / High
    high_risk_probability: float
    estimated_damage_usd: float
    damage_range_low: float
    damage_range_high: float
    forecast_next_year: str     # Increasing / Stable / Decreasing
    shap_features: List[dict]

class BulkRequest(BaseModel):
    states: List[str] = Field(..., example=["TX", "FL", "LA"])
    disaster_category: str = Field(default="flood")
    year: int = Field(default=2024)

class RegionSummary(BaseModel):
    state: str
    risk_score: float
    risk_tier: str
    estimated_damage_usd: float
    lat: float
    lon: float

# ── US state centroids (lat/lon) ──────────────────────────────
STATE_COORDS = {
    "AL": (32.8, -86.8), "AK": (64.2, -153.4), "AZ": (34.3, -111.1),
    "AR": (34.9, -92.4), "CA": (36.8, -119.4), "CO": (39.0, -105.5),
    "CT": (41.6, -72.7), "DE": (39.0, -75.5),  "FL": (27.8, -81.6),
    "GA": (32.2, -83.4), "HI": (19.9, -155.6), "ID": (44.1, -114.5),
    "IL": (40.0, -89.2), "IN": (39.9, -86.3),  "IA": (42.0, -93.2),
    "KS": (38.5, -98.4), "KY": (37.7, -84.9),  "LA": (31.2, -91.8),
    "ME": (45.4, -69.0), "MD": (39.0, -76.8),  "MA": (42.2, -71.5),
    "MI": (44.6, -84.5), "MN": (46.4, -93.1),  "MS": (32.7, -89.7),
    "MO": (38.3, -92.5), "MT": (47.0, -110.0), "NE": (41.5, -99.9),
    "NV": (39.3, -116.6),"NH": (43.7, -71.6),  "NJ": (40.1, -74.5),
    "NM": (34.8, -106.2),"NY": (42.2, -74.9),  "NC": (35.6, -79.4),
    "ND": (47.5, -100.5),"OH": (40.4, -82.8),  "OK": (35.6, -96.9),
    "OR": (43.9, -120.6),"PA": (40.6, -77.2),  "RI": (41.7, -71.6),
    "SC": (33.9, -80.9), "SD": (44.4, -100.2), "TN": (35.9, -86.4),
    "TX": (31.1, -97.6), "UT": (39.3, -111.1), "VT": (44.0, -72.7),
    "VA": (37.5, -79.0), "WA": (47.4, -120.5), "WV": (38.6, -80.6),
    "WI": (44.3, -89.7), "WY": (43.0, -107.6),
}

# ── Helper: build feature vector ─────────────────────────────
def build_feature_vector(req: RiskRequest) -> np.ndarray:
    meta = MODELS.get("meta", {})
    features = meta.get("features", [])

    le_state    = MODELS.get("le_state")
    le_category = MODELS.get("le_category")

    state_enc = 0
    cat_enc   = 0

    if le_state and req.state in le_state.classes_:
        state_enc = int(le_state.transform([req.state])[0])
    if le_category and req.disaster_category in le_category.classes_:
        cat_enc = int(le_category.transform([req.disaster_category])[0])

    feature_map = {
        "year":                 req.year,
        "years_since_2000":     req.year - 2000,
        "decade":               (req.year // 10) * 10,
        "state_enc":            state_enc,
        "category_enc":         cat_enc,
        "event_count":          req.event_count,
        "mean_damage":          req.mean_damage,
        "rolling_5yr_events":   req.rolling_5yr_events,
        "rolling_5yr_damage":   req.rolling_5yr_damage,
        "damage_yoy":           req.damage_yoy,
        "total_deaths":         req.total_deaths,
        "total_injuries":       req.total_injuries,
        "mean_lat":             req.mean_lat,
        "mean_lon":             req.mean_lon,
    }

    return np.array([[feature_map.get(f, 0) for f in features]])

# ── Tier helper ───────────────────────────────────────────────
def get_tier(score: float) -> str:
    if score >= 65: return "High"
    if score >= 35: return "Medium"
    return "Low"

# ── ROUTES ───────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ClimateRisk API running", "version": "1.0.0"}

@app.get("/health")
def health():
    return {
        "status": "ok",
        "models_loaded": "classifier" in MODELS,
        "features": len(MODELS.get("meta", {}).get("features", []))
    }

@app.post("/predict", response_model=RiskResponse)
def predict(req: RiskRequest):
    """
    Single region risk prediction.
    Returns risk score, tier, estimated damage range, and SHAP features.
    """
    clf  = MODELS.get("classifier")
    reg  = MODELS.get("regressor")
    fore = MODELS.get("forecaster")

    # If models not loaded → return mock (useful during dev before training)
    if not clf or not reg:
        return _mock_response(req)

    X = build_feature_vector(req)

    # Risk probability
    prob = float(clf.predict_proba(X)[0][1])
    risk_score = round(prob * 100, 1)

    # Damage prediction (log scale → undo)
    log_damage = float(reg.predict(X)[0])
    damage_usd = float(np.expm1(log_damage))
    damage_low  = damage_usd * 0.75
    damage_high = damage_usd * 1.35

    # Trend forecast
    fore_prob = float(fore.predict_proba(X)[0][1])
    if fore_prob > 0.6:   trend = "Increasing"
    elif fore_prob < 0.4: trend = "Decreasing"
    else:                 trend = "Stable"

    # SHAP top features (from pre-computed meta)
    shap_features = MODELS.get("meta", {}).get("shap_top_features", [])

    return RiskResponse(
        state=req.state,
        disaster_category=req.disaster_category,
        year=req.year,
        risk_score=risk_score,
        risk_tier=get_tier(risk_score),
        high_risk_probability=round(prob, 4),
        estimated_damage_usd=round(damage_usd, 2),
        damage_range_low=round(damage_low, 2),
        damage_range_high=round(damage_high, 2),
        forecast_next_year=trend,
        shap_features=shap_features,
    )

@app.post("/predict/bulk", response_model=List[RegionSummary])
def predict_bulk(req: BulkRequest):
    """
    Predict risk for multiple states at once — used to populate the map.
    """
    results = []
    for state in req.states:
        coords = STATE_COORDS.get(state, (39.0, -98.0))
        single_req = RiskRequest(
            state=state,
            disaster_category=req.disaster_category,
            year=req.year,
            mean_lat=coords[0],
            mean_lon=coords[1],
        )
        pred = predict(single_req)
        results.append(RegionSummary(
            state=state,
            risk_score=pred.risk_score,
            risk_tier=pred.risk_tier,
            estimated_damage_usd=pred.estimated_damage_usd,
            lat=coords[0],
            lon=coords[1],
        ))
    return results

@app.get("/states")
def list_states():
    """Return all available states with coordinates."""
    return [
        {"state": k, "lat": v[0], "lon": v[1]}
        for k, v in STATE_COORDS.items()
    ]

@app.get("/categories")
def list_categories():
    return ["flood", "wildfire", "drought", "hurricane", "other"]

@app.get("/shap")
def get_shap():
    """Return SHAP feature importance for the classifier."""
    return MODELS.get("meta", {}).get("shap_top_features", [])

# ── Mock response (development mode before models are trained) ─
#
# Risk profiles per state — realistic baselines so mock data is meaningful.
# Each entry: (flood_base, wildfire_base, drought_base, hurricane_base) 0–100
STATE_RISK_PROFILES = {
    "TX": (82, 55, 60, 75), "FL": (78, 40, 35, 90), "LA": (88, 30, 40, 85),
    "CA": (50, 90, 75, 10), "OK": (65, 60, 70, 20), "NC": (70, 45, 40, 72),
    "SC": (68, 42, 38, 70), "GA": (60, 48, 45, 65), "AL": (72, 38, 42, 68),
    "MS": (80, 32, 45, 74), "AR": (75, 35, 55, 30), "TN": (65, 38, 40, 25),
    "MO": (62, 40, 58, 18), "KS": (45, 50, 72, 12), "NE": (50, 45, 68, 8),
    "IA": (55, 30, 60, 5),  "IL": (58, 28, 52, 8),  "IN": (52, 25, 48, 6),
    "OH": (48, 22, 42, 5),  "MI": (44, 32, 35, 4),  "WI": (46, 35, 38, 3),
    "MN": (48, 38, 45, 2),  "ND": (52, 30, 65, 1),  "SD": (48, 35, 62, 1),
    "MT": (38, 70, 58, 1),  "WY": (30, 65, 55, 1),  "CO": (35, 72, 60, 2),
    "NM": (28, 68, 72, 2),  "AZ": (25, 65, 80, 3),  "UT": (30, 70, 65, 1),
    "NV": (22, 62, 75, 2),  "ID": (40, 75, 55, 1),  "OR": (55, 80, 48, 8),
    "WA": (58, 75, 42, 6),  "AK": (42, 48, 30, 2),  "HI": (60, 35, 40, 55),
    "NY": (55, 25, 30, 35), "PA": (52, 22, 28, 30), "NJ": (60, 20, 25, 45),
    "CT": (58, 18, 22, 42), "MA": (56, 18, 20, 40), "RI": (55, 16, 18, 38),
    "NH": (48, 20, 22, 32), "VT": (50, 22, 25, 28), "ME": (45, 25, 28, 30),
    "MD": (62, 20, 28, 48), "VA": (65, 28, 32, 52), "WV": (58, 30, 35, 20),
    "KY": (62, 28, 38, 15), "DE": (64, 18, 24, 50),
}

CATEGORY_IDX = {"flood": 0, "wildfire": 1, "drought": 2, "hurricane": 3}

# Year trend: risk has been generally increasing ~1.5% per year since 2000
YEAR_TREND = 0.015

def _mock_response(req: RiskRequest) -> RiskResponse:
    import random

    profile = STATE_RISK_PROFILES.get(req.state, (45, 45, 45, 25))
    cat_idx = CATEGORY_IDX.get(req.disaster_category, 0)
    base_score = profile[cat_idx]

    # Add year trend + per-state-year noise (seeded so same inputs = same output)
    seed = hash(f"{req.state}_{req.disaster_category}_{req.year}")
    rng = random.Random(seed)

    year_delta = (req.year - 2000) * YEAR_TREND * 100
    noise = rng.uniform(-8, 8)
    score = round(min(98, max(2, base_score + year_delta + noise)), 1)

    # Damage scales with state size + risk score
    # Bigger/more exposed states get bigger numbers
    base_damage_m = (score / 100) ** 1.8 * rng.uniform(800, 12000)  # in $M
    damage = base_damage_m * 1_000_000

    # Trend: compare to 2 years ago
    seed_prev = hash(f"{req.state}_{req.disaster_category}_{req.year - 2}")
    rng_prev = random.Random(seed_prev)
    year_delta_prev = (req.year - 2 - 2000) * YEAR_TREND * 100
    noise_prev = rng_prev.uniform(-8, 8)
    prev_score = min(98, max(2, base_score + year_delta_prev + noise_prev))

    diff = score - prev_score
    if diff > 3:    trend = "Increasing"
    elif diff < -3: trend = "Decreasing"
    else:           trend = "Stable"

    # SHAP features — vary by category
    shap_by_cat = {
        "flood":     [("elevation", 31), ("rainfall_trend", 24), ("coast_proximity", 19), ("property_density", 14), ("temp_anomaly", 12)],
        "wildfire":  [("vegetation_density", 34), ("temp_anomaly", 27), ("drought_index", 18), ("wind_speed", 12), ("elevation", 9)],
        "drought":   [("rainfall_deficit", 38), ("temp_anomaly", 25), ("soil_moisture", 17), ("elevation", 12), ("crop_area", 8)],
        "hurricane": [("coast_proximity", 40), ("sea_surface_temp", 26), ("elevation", 16), ("population_density", 11), ("wind_exposure", 7)],
    }
    raw_shap = shap_by_cat.get(req.disaster_category, shap_by_cat["flood"])
    # Add small noise to importances so two states differ slightly
    shap_features = []
    total = 0
    for feat, pct in raw_shap:
        noisy = round(pct + rng.uniform(-3, 3), 1)
        shap_features.append({"feature": feat, "importance_pct": max(1, noisy)})
        total += noisy
    # Normalise to 100
    for s in shap_features:
        s["importance_pct"] = round(s["importance_pct"] / total * 100, 1)

    return RiskResponse(
        state=req.state,
        disaster_category=req.disaster_category,
        year=req.year,
        risk_score=score,
        risk_tier=get_tier(score),
        high_risk_probability=round(score / 100, 4),
        estimated_damage_usd=round(damage, 2),
        damage_range_low=round(damage * 0.72, 2),
        damage_range_high=round(damage * 1.40, 2),
        forecast_next_year=trend,
        shap_features=shap_features,
    )