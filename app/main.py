# app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import sys
import os

# Add current directory to path (ensures imports work on Render)
sys.path.append(os.path.dirname(__file__))

from price_utils import get_nearby_districts, fetch_crop_prices, analyze_prices

app = FastAPI(title="Crop Price API")

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Input JSON schema
class PriceRequest(BaseModel):
    lat: float
    lon: float
    crop: str


@app.post("/prices")
async def get_prices(request: PriceRequest) -> Dict[str, Any]:
    """
    Get crop price analysis for nearby districts.
    Input JSON example: { "lat": 13.0, "lon": 77.6, "crop": "Tomato" }
    """
    # 1️⃣ Find nearby districts
    nearby_districts = get_nearby_districts(request.lat, request.lon)
    if not nearby_districts:
        raise HTTPException(status_code=404, detail="No nearby districts found.")

    # 2️⃣ Loop through districts until we find valid price data
    final_result = None
    for state, district, dist in nearby_districts:
        df = fetch_crop_prices(state, request.crop, days=7)
        if not df.empty:
            result = analyze_prices(df, request.crop)
            if "error" not in result:
                final_result = {
                    "input": {"lat": request.lat, "lon": request.lon, "crop": request.crop},
                    "closest_district": {"state": state, "district": district, "distance_km": round(dist, 2)},
                    **result
                }
                break

    if not final_result:
        raise HTTPException(status_code=404, detail=f"No valid price data for {request.crop}")

    return final_result
