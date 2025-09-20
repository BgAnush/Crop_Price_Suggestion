from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from .utils import get_nearby_districts, fetch_crop_prices, analyze_prices

app = FastAPI(title="Crop Price Analyzer API")

# ✅ Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or restrict to ["http://localhost:8081", "https://your-frontend.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Welcome to Crop Price Analyzer API 🚀"}

@app.get("/prices")
def get_prices(lat: float = Query(...), lon: float = Query(...), crop: str = Query(...)):
    nearby_districts = get_nearby_districts(lat, lon)
    if not nearby_districts:
        return {"error": "No nearby districts found."}

    states_to_check = sorted(set([s for s, _, _ in nearby_districts]))
    for state in states_to_check:
        df_state = fetch_crop_prices(state, crop.title().strip())
        if df_state.empty:
            continue

        nearby_names = [d for s, d, _ in nearby_districts if s == state]
        df_nearby = df_state[df_state["District"].isin(nearby_names)]

        if df_nearby.empty:
            continue

        return analyze_prices(df_nearby, crop)

    return {"error": f"No {crop} records found in nearby states (last 7 days)."}
