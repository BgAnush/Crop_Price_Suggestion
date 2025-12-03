import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
URL = os.getenv("BASE_URL")

def fetch_crop_prices(state: str, crop: str, months: int = 4):
    """
    Fetch crop prices for the last `months` months (default: 4 months).
    """
    days = months * 30     # approx 4 months = 120 days
    today = datetime.today()

    # Generate date list for past X days
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
            resp = requests.get(URL, params=params)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"Error fetching data for {d}: {e}")
            continue

        records = data.get("records", [])
        
        for r in records:
            all_records.append({
                "State": r.get("State"),
                "District": r.get("District"),
                "Market": r.get("Market"),
                "Arrival_Date": r.get("Arrival_Date"),
                "Modal_Price": r.get("Modal_Price")
            })

    df = pd.DataFrame(all_records)
    return df
