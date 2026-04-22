# ============================================================
# CLIMATERISK — PHASE 2: TRAIN ALL 3 ML MODELS
# Run after 01_data_pipeline.py
# ============================================================

# ── CELL 1: Install ──────────────────────────────────────────
# !pip install xgboost lightgbm shap scikit-learn joblib matplotlib seaborn

# ── CELL 2: Imports ──────────────────────────────────────────
import pandas as pd
import numpy as np
import joblib
import shap
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings("ignore")

from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import (
    classification_report, roc_auc_score, mean_absolute_error,
    mean_squared_error, r2_score, confusion_matrix
)
from xgboost import XGBClassifier, XGBRegressor

os.makedirs("models", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

# ── CELL 3: Load data ────────────────────────────────────────
master = pd.read_csv("data/processed/master_dataset.csv")
print(f"Loaded: {master.shape}")
print(master.dtypes)
print(master.head(3))

# ── CELL 4: Feature engineering ──────────────────────────────
# Encode categorical columns
le_state = LabelEncoder()
le_cat = LabelEncoder()

master["state_enc"] = le_state.fit_transform(master["state"].astype(str))
master["category_enc"] = le_cat.fit_transform(master["disaster_category"].astype(str))

# Save encoders for backend inference
joblib.dump(le_state, "models/le_state.pkl")
joblib.dump(le_cat,   "models/le_category.pkl")

FEATURES = [
    "year", "years_since_2000", "decade",
    "state_enc", "category_enc",
    "event_count", "mean_damage",
    "rolling_5yr_events", "rolling_5yr_damage",
    "damage_yoy", "total_deaths", "total_injuries",
    "mean_lat", "mean_lon"
]
# Only keep features that exist
FEATURES = [f for f in FEATURES if f in master.columns]
print(f"\nUsing {len(FEATURES)} features: {FEATURES}")

X = master[FEATURES].fillna(0)
y_class = master["high_risk"]                          # classifier target
y_reg   = np.log1p(master["total_damage"])             # regression target (log scale)

# ── CELL 5: MODEL 1 — Disaster Risk Classifier (XGBoost) ─────
print("\n" + "="*50)
print("MODEL 1: Disaster Risk Classifier")
print("="*50)

X_train, X_test, y_train_c, y_test_c = train_test_split(
    X, y_class, test_size=0.2, random_state=42, stratify=y_class
)

clf = XGBClassifier(
    n_estimators=400,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    scale_pos_weight=(y_train_c == 0).sum() / (y_train_c == 1).sum(),
    use_label_encoder=False,
    eval_metric="logloss",
    random_state=42,
    n_jobs=-1
)

clf.fit(
    X_train, y_train_c,
    eval_set=[(X_test, y_test_c)],
    verbose=50
)

y_pred_c  = clf.predict(X_test)
y_prob_c  = clf.predict_proba(X_test)[:, 1]

print("\nClassification Report:")
print(classification_report(y_test_c, y_pred_c))
print(f"ROC-AUC: {roc_auc_score(y_test_c, y_prob_c):.4f}")

# Cross-validation
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(clf, X, y_class, cv=cv, scoring="roc_auc", n_jobs=-1)
print(f"5-fold CV AUC: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

# Confusion matrix plot
fig, ax = plt.subplots(figsize=(5, 4))
cm = confusion_matrix(y_test_c, y_pred_c)
sns.heatmap(cm, annot=True, fmt="d", cmap="Greens", ax=ax)
ax.set_title("Classifier Confusion Matrix")
ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
plt.tight_layout()
plt.savefig("outputs/classifier_confusion_matrix.png", dpi=150)
plt.show()

joblib.dump(clf, "models/risk_classifier.pkl")
print("✓ Saved: models/risk_classifier.pkl")

# ── CELL 6: MODEL 2 — Financial Damage Regressor ─────────────
print("\n" + "="*50)
print("MODEL 2: Financial Damage Regressor")
print("="*50)

X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(
    X, y_reg, test_size=0.2, random_state=42
)

reg = XGBRegressor(
    n_estimators=500,
    max_depth=6,
    learning_rate=0.04,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1
)

reg.fit(
    X_train_r, y_train_r,
    eval_set=[(X_test_r, y_test_r)],
    verbose=50
)

y_pred_r = reg.predict(X_test_r)

# Convert back from log scale for interpretable metrics
y_pred_r_orig = np.expm1(y_pred_r)
y_test_r_orig = np.expm1(y_test_r)

mae  = mean_absolute_error(y_test_r_orig, y_pred_r_orig)
rmse = np.sqrt(mean_squared_error(y_test_r_orig, y_pred_r_orig))
r2   = r2_score(y_test_r, y_pred_r)

print(f"\nMAE:  ${mae:,.0f}")
print(f"RMSE: ${rmse:,.0f}")
print(f"R²:   {r2:.4f}")

# Predicted vs actual plot
fig, ax = plt.subplots(figsize=(6, 5))
ax.scatter(y_test_r, y_pred_r, alpha=0.3, s=10, color="#1D9E75")
ax.plot([y_test_r.min(), y_test_r.max()],
        [y_test_r.min(), y_test_r.max()], 'r--', lw=1.5)
ax.set_xlabel("Actual log(damage)")
ax.set_ylabel("Predicted log(damage)")
ax.set_title("Regressor: Predicted vs Actual")
plt.tight_layout()
plt.savefig("outputs/regressor_pred_vs_actual.png", dpi=150)
plt.show()

joblib.dump(reg, "models/damage_regressor.pkl")
print("✓ Saved: models/damage_regressor.pkl")

# ── CELL 7: MODEL 3 — Trend Forecaster (state+category level) ─
print("\n" + "="*50)
print("MODEL 3: Risk Trend Forecaster (next-year risk score)")
print("="*50)

# Build a next-year prediction target
# For each state+category, predict next year's high_risk
trend = master.sort_values(["state", "disaster_category", "year"]).copy()
trend["next_year_high_risk"] = trend.groupby(
    ["state", "disaster_category"]
)["high_risk"].shift(-1)
trend = trend.dropna(subset=["next_year_high_risk"])
trend["next_year_high_risk"] = trend["next_year_high_risk"].astype(int)

X_trend = trend[FEATURES].fillna(0)
y_trend  = trend["next_year_high_risk"]

X_tr, X_te, y_tr, y_te = train_test_split(
    X_trend, y_trend, test_size=0.2, random_state=42, stratify=y_trend
)

forecaster = XGBClassifier(
    n_estimators=300,
    max_depth=5,
    learning_rate=0.06,
    subsample=0.8,
    colsample_bytree=0.8,
    scale_pos_weight=(y_tr == 0).sum() / (y_tr == 1).sum(),
    use_label_encoder=False,
    eval_metric="logloss",
    random_state=42,
    n_jobs=-1
)

forecaster.fit(X_tr, y_tr, eval_set=[(X_te, y_te)], verbose=50)

y_pred_f = forecaster.predict(X_te)
y_prob_f = forecaster.predict_proba(X_te)[:, 1]

print("\nTrend Forecaster Classification Report:")
print(classification_report(y_te, y_pred_f))
print(f"ROC-AUC: {roc_auc_score(y_te, y_prob_f):.4f}")

joblib.dump(forecaster, "models/risk_forecaster.pkl")
print("✓ Saved: models/risk_forecaster.pkl")

# ── CELL 8: SHAP Explainability ──────────────────────────────
print("\n" + "="*50)
print("SHAP Feature Importance (Classifier)")
print("="*50)

explainer = shap.TreeExplainer(clf)
shap_values = explainer.shap_values(X_test[:500])   # subset for speed

# Summary plot
shap.summary_plot(
    shap_values, X_test[:500],
    feature_names=FEATURES, show=False
)
plt.tight_layout()
plt.savefig("outputs/shap_summary.png", dpi=150, bbox_inches="tight")
plt.show()
print("✓ Saved: outputs/shap_summary.png")

# Save SHAP mean importance as JSON for the frontend
shap_importance = pd.DataFrame({
    "feature": FEATURES,
    "importance": np.abs(shap_values).mean(axis=0)
}).sort_values("importance", ascending=False)

shap_importance["importance_pct"] = (
    shap_importance["importance"] / shap_importance["importance"].sum() * 100
).round(1)

shap_importance.to_json("outputs/shap_importance.json", orient="records")
print("\nSHAP importance:")
print(shap_importance.head(10))

# ── CELL 9: Save feature list for backend ────────────────────
import json

model_meta = {
    "features": FEATURES,
    "state_classes": list(le_state.classes_),
    "category_classes": list(le_cat.classes_),
    "damage_threshold_70pct": float(master["total_damage"].quantile(0.70)),
    "shap_top_features": shap_importance.head(6)[["feature", "importance_pct"]].to_dict(orient="records")
}

with open("models/model_meta.json", "w") as f:
    json.dump(model_meta, f, indent=2)

print("\n✓ Saved: models/model_meta.json")
print("\n🎉 ALL MODELS TRAINED. Download the 'models/' folder to use in the backend.")
print("Files to download:")
print("  models/risk_classifier.pkl")
print("  models/damage_regressor.pkl")
print("  models/risk_forecaster.pkl")
print("  models/le_state.pkl")
print("  models/le_category.pkl")
print("  models/model_meta.json")
print("  outputs/shap_importance.json")