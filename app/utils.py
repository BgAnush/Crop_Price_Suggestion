import requests
import pandas as pd
from datetime import datetime, timedelta
from geopy.distance import geodesic
from .config import API_KEY, URL, MAX_DISTANCE_KM

# Load coordinates
district_coords_df = pd.read_csv("app/Coordinate_Dataset.csv")

def get_nearby_districts(lat: float, lon: float, max_distance_km: int = MAX_DISTANCE_KM):
    nearby = []
    for _, row in district_coords_df.iterrows():
        dlat, dlon = row["Latitude"], row["Longitude"]
        dist = geodesic((lat, lon), (dlat, dlon)).km
        if dist <= max_distance_km:
            nearby.append((row["State"], row["District"], dist))
    return sorted(nearby, key=lambda x: x[2])

def fetch_crop_prices(state: str, crop: str, days: int = 7):
    today = datetime.today()
    dates = [(today - timedelta(days=i)).strftime("%d-%m-%Y") for i in range(1, days+1)]
    
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
        resp = requests.get(URL, params=params).json()
        records = resp.get("records", [])
        for r in records:
            all_records.append({
                "State": r.get("State"),
                "District": r.get("District"),
                "Market": r.get("Market"),
                "Arrival_Date": r.get("Arrival_Date"),
                "Modal_Price": r.get("Modal_Price")
            })
    return pd.DataFrame(all_records)

def analyze_prices(df, crop: str):
    df["Modal_Price_num"] = pd.to_numeric(df["Modal_Price"], errors="coerce")
    df["Arrival_Date_dt"] = pd.to_datetime(df["Arrival_Date"], format="%d/%m/%Y", errors="coerce")
    df = df.dropna(subset=["Modal_Price_num", "Arrival_Date_dt"])

    df_latest = df.sort_values("Arrival_Date_dt").groupby("Market").tail(1)
    df_top5 = df_latest.sort_values("Modal_Price_num", ascending=False).head(5)

    prices_quintal = df_top5["Modal_Price_num"].tolist()
    prices_kg = [p/100 for p in prices_quintal]

    prices_kg_sorted = sorted(prices_kg)
    min_price = prices_kg_sorted[0]
    max_price = prices_kg_sorted[-1]
    median_price = prices_kg_sorted[len(prices_kg_sorted)//2]

    return {
        "top5": df_top5[["State", "District", "Market", "Arrival_Date", "Modal_Price"]].to_dict(orient="records"),
        "analysis": {
            "min_price": round(min_price, 2),
            "median_price": round(median_price, 2),
            "max_price": round(max_price, 2),
            "suggested_profit_range": "Add ₹5–10 per kg for profit"
        }
    }
