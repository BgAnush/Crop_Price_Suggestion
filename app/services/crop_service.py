import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
URL = os.getenv("BASE_URL")

def fetch_crop_prices(state: str, crop: str):
    """
    Fetch ALL available crop price data for the given state + crop.
    No date filters are applied.
    """
    all_records = []
    offset = 0
    limit = 5000  # maximum supported by API

    while True:
        params = {
            "api-key": API_KEY,
            "format": "json",
            "limit": limit,
            "offset": offset,
            "filters[State]": state,
            "filters[Commodity]": crop
        }

        try:
            resp = requests.get(URL, params=params)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"Error fetching data: {e}")
            break

        records = data.get("records", [])

        # Stop if no more data
        if not records:
            break

        # Extract required fields
        for r in records:
            all_records.append({
                "State": r.get("State"),
                "District": r.get("District"),
                "Market": r.get("Market"),
                "Arrival_Date": r.get("Arrival_Date"),
                "Modal_Price": r.get("Modal_Price")
            })

        offset += limit  # go to next batch

    df = pd.DataFrame(all_records)
    return df
