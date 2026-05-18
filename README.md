# ClimateRisk 

 A full-stack machine learning system that predicts climate disaster risk and estimates financial exposure across all 50 US states — combining XGBoost classification, damage regression, and trend forecasting into a single interactive dashboard.

---

## Overview

Most climate tools stop at "will a disaster happen here." ClimateRisk goes further — it quantifies **how much it will cost** and whether risk is **increasing or decreasing** over time. Three separate ML models are fused into one pipeline, trained on 1.2M+ real disaster records from NOAA and FEMA.

---

## Features

- **Risk classification** — predicts high/medium/low disaster risk per state and disaster type
- **Financial exposure estimation** — outputs damage range with confidence interval
- **Trend forecasting** — predicts whether next year's risk is increasing, stable, or decreasing
- **SHAP explainability** — shows which features drove each prediction (not just a score)
- **Interactive heatmap** — Leaflet.js map with color-coded risk circles across all 50 states
- **Side-by-side comparison** — compare any two states across disaster types and years
- **Mock mode** — backend runs with realistic seeded data before real models are trained

---

## ML Architecture

```
NOAA Storm Events (1.2M rows)                FEMA Public Assistance (1M rows)
        │                                               │
        └──────────────── Feature Engineering ──────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
    Disaster Risk            Financial Damage       Trend
    Classifier               Regressor              Forecaster
    (XGBoost)                (XGBoost)              (XGBoost)
    → risk score             → damage $$$           → Increasing /
    → High/Med/Low           → range low/high         Stable /
                                                       Decreasing
              └────────────────────┼────────────────────┘
                                   │
                            SHAP Explainer
                                   │
                            FastAPI Backend
                                   │
                          React + Leaflet Frontend
```

### Model details

| Model | Type | Target | Key features |
|---|---|---|---|
| Risk classifier | XGBoost binary | High-risk (top 30% damage) | Elevation, coastal proximity, rolling 5yr events, damage YoY |
| Damage regressor | XGBoost regression | log(total_damage_USD) | All classifier features + FEMA obligated amounts |
| Trend forecaster | XGBoost binary | Next-year high risk | Current year features shifted by 1 year |

---

## Dataset

| Source | Size | Used for |
|---|---|---|
| NOAA Storm Events (2000–2023) | 1.2M+ rows | Primary training — event counts, damage, deaths |
| FEMA Public Assistance Projects | ~1M rows | Financial exposure labels |
| FEMA Disaster Declarations | ~70k rows | Disaster categorisation |

All datasets are free and publicly available. No synthetic or Kaggle toy data.

---

## Tech Stack

**ML & Data**
`Python` `XGBoost` `scikit-learn` `SHAP` `pandas` `NumPy` `Google Colab`

**Backend**
`FastAPI` `Uvicorn` `Pydantic` `joblib`

**Frontend**
`React` `Vite` `Leaflet.js` `Recharts` `React Router`

---

## Project Structure

```
climaterisk/
├── colab/
│   ├── 01_data_pipeline.py     
│   └── 02_train_models.py      
├── backend/
│   ├── main.py                
│   ├── requirements.txt
│   └── models/                 
└── frontend/
    ├── src/
    │   ├── components/         
    │   └── pages/              
    ├── package.json
    └── vite.config.js
```

---

## Getting Started

### 1. Train models (Google Colab)

```bash
# In a new Colab notebook, paste and run:
# 01_data_pipeline.py  →  downloads + cleans data (~10 min)
# 02_train_models.py   →  trains models + exports .pkl files (~8 min)

# Download these files from Colab when done:
models/risk_classifier.pkl
models/damage_regressor.pkl
models/risk_forecaster.pkl
models/le_state.pkl
models/le_category.pkl
models/model_meta.json
```

### 2. Run the backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Place downloaded .pkl files in backend/models/
uvicorn main:app --reload --port 8000
```

API docs auto-generated at `http://localhost:8000/docs`


### 3. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Model load status |
| `POST` | `/predict` | Single state prediction |
| `POST` | `/predict/bulk` | All states → map data |
| `GET` | `/shap` | Feature importance |
| `GET` | `/states` | All states with coordinates |
| `GET` | `/docs` | Swagger UI |

---

## Screenshots

<img width="1910" height="889" alt="image" src="https://github.com/user-attachments/assets/51d874aa-9ab4-4edd-a7ed-a2c0bf3cf409" />


<img width="1259" height="884" alt="image" src="https://github.com/user-attachments/assets/196a57dc-30b6-443c-aeeb-b53cf7124f2c" />




---
