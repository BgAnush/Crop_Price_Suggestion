import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
URL = os.getenv("BASE_URL")

def fetch_all_crop_data(state: str, district: str, crop: str):
    """
    Fetch ALL available historical data (no date filter) 
    using automatic pagination until all records are retrieved.
    """
    all_records = []
    offset = 0
    limit = 5000  # API max limit

    while True:
        params = {
            "api-key": API_KEY,
            "format": "json",
            "limit": limit,
            "offset": offset,
            "filters[State]": state,
            "filters[District]": district,
            "filters[Commodity]": crop
        }

        try:
            response = requests.get(URL, params=params)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"Error: {e}")
            break

        records = data.get("records", [])

        # Stop when no more data available
        if not records:
            break

        for r in records:
            all_records.append({
                "State": r.get("State"),
                "District": r.get("District"),
                "Market": r.get("Market"),
                "Commodity": r.get("Commodity"),
                "Variety": r.get("Variety"),
                "Grade": r.get("Grade"),
                "Arrival_Date": r.get("Arrival_Date"),
                "Min_Price": r.get("Min_Price"),
                "Max_Price": r.get("Max_Price"),
                "Modal_Price": r.get("Modal_Price"),
                "Commodity_Code": r.get("Commodity_Code")
            })

        offset += limit  # move to next batch

    df = pd.DataFrame(all_records)
    return df
