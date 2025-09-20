import requests
import pandas as pd
from datetime import datetime, timedelta
from geopy.distance import geodesic
from app.config import API_KEY, URL, MAX_DISTANCE_KM

# Load coordinates dataset
district_coords_df = pd.read_csv("app/Coordinate_Dataset.csv")


def get_nearby_districts(lat: float, lon: float, max_distance_km: int = MAX_DISTANCE_KM):
    """Return list of nearby districts within max_distance_km"""
    nearby = []
    for _, row in district_coords_df.iterrows():
        dist = geodesic((lat, lon), (row["Latitude"], row["Longitude"])).km
        if dist <= max_distance_km:
            nearby.append((row["State"], row["District"], dist))
    return sorted(nearby, key=lambda x: x[2])


def fetch_crop_prices(state: str, crop: str, days: int = 7):
    """Fetch crop price data from API for last N days"""
    today = datetime.today()
    dates = [(today - timedelta(days=i)).strftime("%d-%m-%Y") for i in range(1, days + 1)]

    all_records = []
    for d in dates:
        params = {
            "api-key": API_KEY,
            "format": "json",
            "limit": 5000,
            "filters[State]": state,
            "filters[Commodity]": crop,
            "filters[Arrival_Date]": d
        }
        try:
            resp = requests.get(URL, params=params).json()
        except Exception:
            continue
        records = resp.get("records", [])
        for r in records:
            all_records.append({
                "State": r.get("State"),
                "District": r.get("District"),
                "Market": r.get("Market"),
                "Arrival_Date": r.get("Arrival_Date"),
                "Modal_Price": r.get("Modal_Price")  # ₹ per quintal
            })
    return pd.DataFrame(all_records)


def analyze_prices(df, crop: str):
    """Analyze crop prices: top 5 markets and price stats in ₹/kg"""
    df["Modal_Price_num"] = pd.to_numeric(df["Modal_Price"], errors="coerce")
    df["Arrival_Date_dt"] = pd.to_datetime(df["Arrival_Date"], format="%d/%m/%Y", errors="coerce")
    df = df.dropna(subset=["Modal_Price_num", "Arrival_Date_dt"])

    if df.empty:
        return {"error": f"No valid price data for {crop}"}

    # Keep latest per market
    df_latest = df.sort_values("Arrival_Date_dt").groupby("Market").tail(1)
    df_latest["Modal_Price_per_kg"] = df_latest["Modal_Price_num"] / 100  # ₹/kg

    # Top 5 markets
    df_top5 = df_latest.sort_values("Modal_Price_per_kg", ascending=False).head(5)

    # Price stats
    prices = df_top5["Modal_Price_per_kg"].tolist()
    if not prices:
        return {"error": f"No valid price data for {crop}"}

    min_price = round(min(prices), 2)
    max_price = round(max(prices), 2)
    avg_price = round(sum(prices) / len(prices), 2)

    return {
        "top5": df_top5[["State", "District", "Market", "Arrival_Date", "Modal_Price", "Modal_Price_per_kg"]]
                    .to_dict(orient="records"),
        "analysis": {
            "min_price_per_kg": min_price,
            "avg_price_per_kg": avg_price,
            "max_price_per_kg": max_price,
            "suggested_profit_range": "Add ₹5–10 per kg for profit"
        }
    }
