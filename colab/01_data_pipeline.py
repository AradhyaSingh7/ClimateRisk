# ============================================================
# CLIMATERISK — PHASE 1: DATA PIPELINE
# Run this entire file in Google Colab (cell by cell)
# ============================================================

# ── CELL 1: Install dependencies ─────────────────────────────
# !pip install pandas numpy requests geopandas shapely tqdm

# ── CELL 2: Imports ──────────────────────────────────────────
import pandas as pd
import numpy as np
import requests
import zipfile
import io
import os
from tqdm import tqdm

os.makedirs("data/raw", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)
print("Directories ready.")

# ── CELL 3: Download NOAA Storm Events ───────────────────────
# Downloads 2000–2023 — ~1.1M rows total across years
# Each year has 3 files: details, fatalities, locations
# We only need "details" files

NOAA_BASE = "https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/"
YEARS = list(range(2000, 2024))

def download_noaa_year(year):
    """Download NOAA storm events details CSV for a given year."""
    import urllib.request
    import re

    # List files on NOAA server to find exact filename (version changes)
    listing_url = NOAA_BASE
    try:
        with urllib.request.urlopen(listing_url) as response:
            html = response.read().decode()
        # Find the details file for this year
        pattern = rf'StormEvents_details-ftp_v\d+\.\d+_{year}\d{{4}}\.csv\.gz'
        matches = re.findall(pattern, html)
        if not matches:
            print(f"  ⚠ No file found for {year}")
            return None
        filename = matches[-1]  # take latest version
        url = NOAA_BASE + filename
        print(f"  Downloading {filename}...")
        df = pd.read_csv(url, compression='gzip', low_memory=False)
        return df
    except Exception as e:
        print(f"  ✗ Failed {year}: {e}")
        return None

print("Downloading NOAA Storm Events (2000–2023)...")
print("This takes ~5–8 minutes. Go get a coffee ☕")

dfs = []
for year in YEARS:
    print(f"\nYear {year}:")
    df = download_noaa_year(year)
    if df is not None:
        dfs.append(df)

noaa_raw = pd.concat(dfs, ignore_index=True)
noaa_raw.to_csv("data/raw/noaa_storm_events_raw.csv", index=False)
print(f"\n✓ NOAA raw: {len(noaa_raw):,} rows × {noaa_raw.shape[1]} cols")
print(noaa_raw.dtypes)

# ── CELL 4: Download FEMA Disaster Declarations ───────────────
print("\nDownloading FEMA Disaster Declarations...")

# FEMA OpenFEMA API — paginated, returns JSON
fema_url = "https://www.fema.gov/api/open/v2/disasterDeclarationsSummaries"
all_records = []
skip = 0
limit = 1000

while True:
    params = {
        "$limit": limit,
        "$skip": skip,
        "$orderby": "declarationDate asc",
        "$filter": "incidentBeginDate ge '2000-01-01T00:00:00.000z'"
    }
    resp = requests.get(fema_url, params=params, timeout=30)
    batch = resp.json().get("DisasterDeclarationsSummaries", [])
    if not batch:
        break
    all_records.extend(batch)
    skip += limit
    print(f"  Fetched {len(all_records):,} records...", end="\r")

fema_declarations = pd.DataFrame(all_records)
fema_declarations.to_csv("data/raw/fema_declarations_raw.csv", index=False)
print(f"\n✓ FEMA Declarations: {len(fema_declarations):,} rows")

# ── CELL 5: Download FEMA Public Assistance (damage $$$) ──────
print("\nDownloading FEMA Public Assistance Funded Projects...")

pa_url = "https://www.fema.gov/api/open/v1/PublicAssistanceFundedProjectsDetails"
pa_records = []
skip = 0

while True:
    params = {
        "$limit": 1000,
        "$skip": skip,
        "$filter": "declarationDate ge '2000-01-01T00:00:00.000z'"
    }
    resp = requests.get(pa_url, params=params, timeout=60)
    batch = resp.json().get("PublicAssistanceFundedProjectsDetails", [])
    if not batch:
        break
    pa_records.extend(batch)
    skip += 1000
    print(f"  Fetched {len(pa_records):,} PA records...", end="\r")
    if len(pa_records) > 500000:   # cap at 500k for Colab memory
        print("\n  Capped at 500k rows to protect Colab RAM")
        break

fema_pa = pd.DataFrame(pa_records)
fema_pa.to_csv("data/raw/fema_pa_raw.csv", index=False)
print(f"\n✓ FEMA Public Assistance: {len(fema_pa):,} rows")

# ── CELL 6: NOAA Cleaning ────────────────────────────────────
print("\nCleaning NOAA data...")

# Columns we actually need
noaa_cols = [
    "YEAR", "MONTH_NAME", "STATE", "STATE_FIPS", "CZ_NAME",
    "EVENT_TYPE", "BEGIN_LAT", "BEGIN_LON",
    "DAMAGE_PROPERTY", "DAMAGE_CROPS",
    "DEATHS_DIRECT", "DEATHS_INDIRECT",
    "INJURIES_DIRECT", "INJURIES_INDIRECT",
    "MAGNITUDE", "MAGNITUDE_TYPE"
]
noaa = noaa_raw[[c for c in noaa_cols if c in noaa_raw.columns]].copy()

# Parse damage strings like "3.5K", "1.2M", "0" → float
def parse_damage(val):
    if pd.isna(val) or val in ("", "0"):
        return 0.0
    val = str(val).strip().upper()
    multipliers = {"K": 1e3, "M": 1e6, "B": 1e9}
    for suffix, mult in multipliers.items():
        if val.endswith(suffix):
            try:
                return float(val[:-1]) * mult
            except:
                return 0.0
    try:
        return float(val)
    except:
        return 0.0

noaa["damage_property_usd"] = noaa["DAMAGE_PROPERTY"].apply(parse_damage)
noaa["damage_crops_usd"] = noaa["DAMAGE_CROPS"].apply(parse_damage)
noaa["total_damage_usd"] = noaa["damage_property_usd"] + noaa["damage_crops_usd"]
noaa["total_deaths"] = noaa[["DEATHS_DIRECT", "DEATHS_INDIRECT"]].fillna(0).sum(axis=1)
noaa["total_injuries"] = noaa[["INJURIES_DIRECT", "INJURIES_INDIRECT"]].fillna(0).sum(axis=1)

# Standardise event type → disaster category
FLOOD_EVENTS = [
    "Flash Flood", "Flood", "Coastal Flood", "Lakeshore Flood",
    "Storm Surge/Tide", "Tsunami"
]
WILDFIRE_EVENTS = ["Wildfire", "Debris Flow"]
DROUGHT_EVENTS = ["Drought", "Excessive Heat", "Heat"]
HURRICANE_EVENTS = [
    "Hurricane", "Hurricane (Typhoon)", "Tropical Storm",
    "Tropical Depression"
]

def categorise(event):
    if event in FLOOD_EVENTS:      return "flood"
    if event in WILDFIRE_EVENTS:   return "wildfire"
    if event in DROUGHT_EVENTS:    return "drought"
    if event in HURRICANE_EVENTS:  return "hurricane"
    return "other"

noaa["disaster_category"] = noaa["EVENT_TYPE"].apply(categorise)

# Drop rows with no location or no damage info
noaa = noaa.dropna(subset=["BEGIN_LAT", "BEGIN_LON"])
noaa = noaa.rename(columns={
    "YEAR": "year", "STATE": "state", "STATE_FIPS": "state_fips",
    "CZ_NAME": "county", "BEGIN_LAT": "lat", "BEGIN_LON": "lon"
})

# Save
noaa_clean = noaa[[
    "year", "state", "state_fips", "county", "lat", "lon",
    "disaster_category", "total_damage_usd", "total_deaths",
    "total_injuries"
]]
noaa_clean.to_csv("data/processed/noaa_clean.csv", index=False)
print(f"✓ NOAA clean: {len(noaa_clean):,} rows")
print(noaa_clean["disaster_category"].value_counts())

# ── CELL 7: FEMA Cleaning ─────────────────────────────────────
print("\nCleaning FEMA data...")

fema = fema_declarations.copy()

# Normalise column names
fema.columns = [c.lower() for c in fema.columns]

# Keep relevant columns
fema_keep = [
    "disasternumber", "state", "declarationdate",
    "incidenttype", "designateddarea", "fipscode",
    "totalamountihapproved", "totalamounthaapproved",
    "totalobligatedamountpa"
]
fema_keep = [c for c in fema_keep if c in fema.columns]
fema = fema[fema_keep].copy()

# Parse dates
if "declarationdate" in fema.columns:
    fema["declarationdate"] = pd.to_datetime(fema["declarationdate"], errors="coerce")
    fema["year"] = fema["declarationdate"].dt.year

# Disaster type mapping
fema_type_map = {
    "Flood": "flood", "Hurricane": "hurricane",
    "Fire": "wildfire", "Drought": "drought",
    "Tornado": "other", "Severe Storm": "other",
    "Snow": "other", "Earthquake": "other"
}
if "incidenttype" in fema.columns:
    fema["disaster_category"] = fema["incidenttype"].map(fema_type_map).fillna("other")

# Financial columns → numeric
for col in ["totalobligatedamountpa", "totalamountihapproved", "totalamounthaapproved"]:
    if col in fema.columns:
        fema[col] = pd.to_numeric(fema[col], errors="coerce").fillna(0)

fema.to_csv("data/processed/fema_clean.csv", index=False)
print(f"✓ FEMA clean: {len(fema):,} rows")

# ── CELL 8: Build master training dataset ────────────────────
print("\nBuilding master training dataset...")

# Aggregate NOAA by state + year + category
noaa_agg = noaa_clean.groupby(["year", "state", "disaster_category"]).agg(
    event_count=("total_damage_usd", "count"),
    total_damage=("total_damage_usd", "sum"),
    mean_damage=("total_damage_usd", "mean"),
    total_deaths=("total_deaths", "sum"),
    total_injuries=("total_injuries", "sum"),
    mean_lat=("lat", "mean"),
    mean_lon=("lon", "mean")
).reset_index()

# Temporal features
noaa_agg["decade"] = (noaa_agg["year"] // 10) * 10
noaa_agg["years_since_2000"] = noaa_agg["year"] - 2000

# Rolling trend: events per state per category over 5-year window
noaa_agg = noaa_agg.sort_values(["state", "disaster_category", "year"])
noaa_agg["rolling_5yr_events"] = (
    noaa_agg.groupby(["state", "disaster_category"])["event_count"]
    .transform(lambda x: x.rolling(5, min_periods=1).mean())
)
noaa_agg["rolling_5yr_damage"] = (
    noaa_agg.groupby(["state", "disaster_category"])["total_damage"]
    .transform(lambda x: x.rolling(5, min_periods=1).mean())
)

# Damage growth rate (year over year)
noaa_agg["damage_yoy"] = (
    noaa_agg.groupby(["state", "disaster_category"])["total_damage"]
    .pct_change().fillna(0).clip(-2, 10)
)

# Binary risk label: top 30% damage = high risk
threshold = noaa_agg["total_damage"].quantile(0.70)
noaa_agg["high_risk"] = (noaa_agg["total_damage"] >= threshold).astype(int)

# Merge FEMA financial exposure
if "fipscode" in fema.columns and "totalobligatedamountpa" in fema.columns:
    fema_by_state = fema.groupby(["year", "state", "disaster_category"]).agg(
        fema_obligated=("totalobligatedamountpa", "sum")
    ).reset_index()
    master = noaa_agg.merge(fema_by_state, on=["year", "state", "disaster_category"], how="left")
    master["fema_obligated"] = master["fema_obligated"].fillna(0)
else:
    master = noaa_agg.copy()
    master["fema_obligated"] = 0

master.to_csv("data/processed/master_dataset.csv", index=False)
print(f"\n✓ Master dataset: {len(master):,} rows × {master.shape[1]} cols")
print("\nSample:")
print(master.head())
print("\nClass balance (high_risk):")
print(master["high_risk"].value_counts(normalize=True).round(3))