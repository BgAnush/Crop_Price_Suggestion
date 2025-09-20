from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any

from price_utils import get_nearby_districts, fetch_crop_prices, analyze_prices

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PriceRequest(BaseModel):
    lat: float
    lon: float
    crop: str

@app.post("/prices")
async def get_prices(request: PriceRequest) -> Dict[str, Any]:
    nearby_districts = get_nearby_districts(request.lat, request.lon)
    if not nearby_districts:
        raise HTTPException(status_code=404, detail="No nearby districts found.")

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
