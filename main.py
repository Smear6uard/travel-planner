import asyncio
import json
import os
from typing import List, Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="MP1 -- Atlas AI Travel Planner")

app.mount("/static", StaticFiles(directory="static"), name="static")

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY", "")
TOGETHER_API_URL = "https://api.together.xyz/v1/chat/completions"
MODEL = "meta-llama/Llama-3.3-70B-Instruct-Turbo"

TRAVEL_SYSTEM_PROMPT = """You are an elite travel planning expert with encyclopedic knowledge of destinations worldwide. Your name is Atlas.

Your personality: warm, enthusiastic, deeply knowledgeable, and highly detail-oriented.

When a user first reaches out with vague travel intent:
- Ask 2-3 targeted clarifying questions about budget, travel style, dates, or interests before generating a plan.

BUDGET TIERS — strictly follow these per-person per-day spending targets:
- Budget: ~$50–80/person/day total. Hostels or budget guesthouses ($15–35/night), street food and cheap local eateries ($5–15/meal), free or low-cost attractions, public transit only. Grand total should reflect this math.
- Moderate: ~$150–250/person/day total. 3-star hotels ($80–150/night), mid-range restaurants ($15–35/meal), a mix of paid attractions and free activities, some taxis/rideshare. Grand total should reflect this math.
- Luxury: ~$400–800+/person/day total. 4–5 star hotels or boutique properties ($200–600+/night), fine dining ($60–150+/meal), private transfers, premium experiences and tours. Grand total should reflect this math.

Always calculate and display a realistic grand total based on the number of travelers, number of days, and the correct budget tier above. Never assign luxury prices to a Budget trip or budget prices to a Luxury trip.

When you have enough information, generate a rich day-by-day itinerary that includes:
- 🏨 Accommodation recommendations (with price range matching the budget tier)
- 🗺️ Day-by-day activities with timing
- 🍽️ Dining recommendations (breakfast, lunch, dinner) with local specialties
- 🚌 Transportation tips (getting around, airport transfers)
- 💰 Detailed budget breakdown with a grand total that matches the selected tier
- 💡 Insider tips and cultural notes
- ⚠️ Things to avoid or watch out for

CRITICAL FORMAT FOR ITINERARIES: Always use ## Day 1: Title, ## Day 2: Title, etc. as section headers (never bold text like **Day 1**). Use bullet points (-) under each day for activities, meals, and accommodation.

CRITICAL COST FORMAT: Every single bullet point activity, meal, and accommodation MUST end with a cost in parentheses, e.g. ($25), ($120), (free). Always a single number matching the budget tier — never a range like ($50–$80). This applies to every line without exception.

Be specific — always use the full official name for every venue, landmark, restaurant, hotel, and attraction (e.g., "Senso-ji Temple" not "a temple", "Eiffel Tower" not "the tower", "Le Comptoir du Relais" not "a bistro"). Include real place names, neighborhoods, and practical advice. Make the user feel genuinely excited about their trip."""


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]


class ManualPlanRequest(BaseModel):
    destination: str
    start_date: str
    end_date: str
    travelers: int
    budget: str
    interests: List[str]
    special_requests: Optional[str] = ""


# Top travel cities — matched by lowercase name to boost them above generic results
_POPULAR_CITIES = {
    "tokyo", "paris", "london", "new york", "dubai", "singapore", "istanbul",
    "bangkok", "barcelona", "amsterdam", "rome", "vienna", "berlin", "madrid",
    "sydney", "toronto", "los angeles", "chicago", "miami", "las vegas",
    "san francisco", "new orleans", "washington", "boston", "seattle",
    "hong kong", "seoul", "beijing", "shanghai", "kyoto", "osaka", "taipei",
    "kuala lumpur", "bali", "phuket", "cancun", "rio de janeiro", "havana",
    "buenos aires", "sao paulo", "mexico city", "bogota", "lima", "santiago",
    "cairo", "marrakech", "casablanca", "nairobi", "cape town", "johannesburg",
    "prague", "budapest", "lisbon", "brussels", "zurich", "geneva", "venice",
    "florence", "milan", "naples", "athens", "santorini", "dubrovnik", "split",
    "moscow", "st. petersburg", "mumbai", "delhi", "kolkata", "bangalore",
    "reykjavik", "stockholm", "oslo", "copenhagen", "helsinki", "edinburgh",
    "dublin", "glasgow", "manila", "jakarta", "hanoi", "ho chi minh city",
    "yangon", "colombo", "kathmandu", "muscat", "doha", "abu dhabi", "riyadh",
    "seville", "porto", "montreal", "vancouver", "auckland", "melbourne",
    "brisbane", "perth", "denver", "phoenix", "dallas", "houston", "atlanta",
    "portland", "nashville", "austin", "new delhi", "maldives", "zanzibar",
    "accra", "lagos", "addis ababa", "kigali", "dar es salaam", "kampala",
}


def _photon_rank(feature: dict, q_lower: str) -> int:
    props = feature.get("properties", {})
    name = props.get("name", "").lower()
    osm_value = props.get("osm_value", "")
    # Tier 0 — well-known travel city that prefix-matches the query
    if name in _POPULAR_CITIES and name.startswith(q_lower):
        return 0
    # Tier 1 — cities and capitals
    if osm_value in {"city", "capital", "municipality"}:
        return 1
    # Tier 2 — countries (good travel destinations but less specific)
    if osm_value == "country":
        return 2
    # Tier 3 — provinces, states, regions
    if osm_value in {"province", "state", "administrative", "county", "region",
                     "district", "federal_state", "department", "borough"}:
        return 3
    return 4


@app.get("/api/suggestions")
async def get_suggestions(q: str = ""):
    if len(q.strip()) < 2:
        return {"suggestions": []}

    # Photon is built for autocomplete and always returns English with lang=en
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(
                "https://photon.komoot.io/api/",
                params={"q": q, "lang": "en", "limit": 20},
                headers={"User-Agent": "AtlasTravelPlanner/1.0"},
            )
            features = response.json().get("features", [])
    except Exception:
        features = []

    ALLOWED_VALUES = {
        "city", "town", "village", "country", "municipality", "borough",
        "administrative", "capital", "province", "state", "county",
        "region", "district", "federal_state", "department",
    }

    q_lower = q.strip().lower()
    # Stable sort preserves Photon's relevance order within each tier
    features.sort(key=lambda f: _photon_rank(f, q_lower))

    suggestions = []
    seen: set = set()
    for feature in features:
        props = feature.get("properties", {})
        osm_key = props.get("osm_key", "")
        osm_value = props.get("osm_value", "")

        if osm_key not in ("place", "boundary"):
            continue
        if osm_value not in ALLOWED_VALUES:
            continue

        name = props.get("name", "")
        state = props.get("state", "")
        country = props.get("country", "")
        if not name or not country:
            continue

        # Avoid "China, China" when the place name is the country name
        if name == country:
            label = name
        else:
            parts = [name]
            if state and state != name and state != country:
                parts.append(state)
            parts.append(country)
            label = ", ".join(parts)

        if label not in seen:
            seen.add(label)
            suggestions.append(label)
        if len(suggestions) == 5:
            break

    return {"suggestions": suggestions}


@app.get("/api/geocode")
async def geocode(q: str = ""):
    if not q.strip():
        return {"lat": None, "lon": None}
    async with httpx.AsyncClient(timeout=8.0) as client:
        resp = await client.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": q, "format": "json", "limit": 1},
            headers={"User-Agent": "AtlasTravelPlanner/1.0 (csc394@depaul.edu)"},
        )
        data = resp.json()
    if not data:
        return {"lat": None, "lon": None}
    return {"lat": float(data[0]["lat"]), "lon": float(data[0]["lon"])}


class BatchGeocodeRequest(BaseModel):
    queries: List[str]


@app.post("/api/geocode/batch")
async def geocode_batch(request: BatchGeocodeRequest):
    """Geocode up to 50 place queries using Photon (OpenStreetMap-based, no strict rate limit)."""
    results = []
    async with httpx.AsyncClient(timeout=6.0) as client:
        for q in request.queries[:50]:
            if not q.strip():
                results.append({"lat": None, "lon": None})
                continue
            try:
                resp = await client.get(
                    "https://photon.komoot.io/api/",
                    params={"q": q, "limit": 1, "lang": "en"},
                    headers={"User-Agent": "AtlasTravelPlanner/1.0"},
                )
                features = resp.json().get("features", [])
                if features:
                    coords = features[0]["geometry"]["coordinates"]  # [lon, lat]
                    results.append({"lat": coords[1], "lon": coords[0]})
                else:
                    results.append({"lat": None, "lon": None})
            except Exception:
                results.append({"lat": None, "lon": None})
            await asyncio.sleep(0.1)
    return {"results": results}


@app.get("/api/weather")
async def get_weather(destination: str, start_date: str = "", end_date: str = ""):
    async with httpx.AsyncClient(timeout=12.0) as client:
        geo = await client.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": destination, "format": "json", "limit": 1},
            headers={"User-Agent": "AtlasTravelPlanner/1.0 (csc394@depaul.edu)"},
        )
        geo_data = geo.json()
        if not geo_data:
            return {"weather": [], "lat": None, "lon": None}

        lat = float(geo_data[0]["lat"])
        lon = float(geo_data[0]["lon"])

        params: dict = {
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,weather_code",
            "timezone": "auto",
            "forecast_days": 16,
        }
        w_resp = await client.get("https://api.open-meteo.com/v1/forecast", params=params)
        w = w_resp.json()

    daily = w.get("daily", {})
    dates = daily.get("time", [])
    maxes = daily.get("temperature_2m_max", [])
    mins = daily.get("temperature_2m_min", [])
    codes = daily.get("weather_code", [])

    def wx_icon(code):
        if code is None: return "🌤️"
        if code == 0: return "☀️"
        if code <= 3: return "⛅"
        if code <= 49: return "🌫️"
        if code <= 67: return "🌧️"
        if code <= 77: return "❄️"
        return "⛈️"

    result = [
        {
            "date": dates[i],
            "max": round(maxes[i]) if i < len(maxes) and maxes[i] is not None else None,
            "min": round(mins[i]) if i < len(mins) and mins[i] is not None else None,
            "icon": wx_icon(codes[i] if i < len(codes) else None),
        }
        for i in range(len(dates))
    ]
    return {"weather": result, "lat": lat, "lon": lon}


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    if not TOGETHER_API_KEY:
        raise HTTPException(status_code=500, detail="TOGETHER_API_KEY not set.")

    messages = [{"role": "system", "content": TRAVEL_SYSTEM_PROMPT}]
    messages += [{"role": m.role, "content": m.content} for m in request.messages]

    async def generate():
        async with httpx.AsyncClient(timeout=90.0) as client:
            async with client.stream(
                "POST",
                TOGETHER_API_URL,
                headers={
                    "Authorization": f"Bearer {TOGETHER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": MODEL,
                    "messages": messages,
                    "max_tokens": 3000,
                    "temperature": 0.75,
                    "stream": True,
                },
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            yield "data: [DONE]\n\n"
                            return
                        try:
                            chunk = json.loads(data)
                            delta = chunk["choices"][0]["delta"]
                            if delta.get("content"):
                                payload = json.dumps({"content": delta["content"]})
                                yield f"data: {payload}\n\n"
                        except Exception:
                            pass

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/api/plan/manual")
async def manual_plan(request: ManualPlanRequest):
    if not TOGETHER_API_KEY:
        raise HTTPException(status_code=500, detail="TOGETHER_API_KEY not set.")

    interests_str = ", ".join(request.interests) if request.interests else "general sightseeing"
    budget_guide = {
        "Budget":   "~$50–80/person/day — hostels/budget hotels, street food, public transit, free attractions",
        "Moderate": "~$150–250/person/day — 3-star hotels, mid-range restaurants, mix of paid and free activities",
        "Luxury":   "~$400–800+/person/day — 4–5 star hotels, fine dining, private transfers, premium experiences",
    }.get(request.budget, f"~{request.budget} level spending")

    prompt = f"""Please create a comprehensive travel itinerary with the following details:

**Destination:** {request.destination}
**Travel Dates:** {request.start_date} to {request.end_date}
**Number of Travelers:** {request.travelers}
**Budget Level:** {request.budget} ({budget_guide})
**Interests:** {interests_str}
**Special Requests:** {request.special_requests or "None"}

Important: All accommodation, dining, and activity costs MUST match the {request.budget} budget tier defined above. Calculate a realistic grand total based on {request.travelers} traveler(s) and the number of trip days.

Generate a full day-by-day itinerary with accommodations, activities, dining, transportation, and a budget breakdown.

CRITICAL FORMATTING — you must follow this structure exactly:
## Day 1: [Title]
## Day 2: [Title]
## Day 3: [Title]
(continue for every day)

Under each ## Day header, use bullet points (-) for every activity, meal, and accommodation. Do NOT use bold (**) as day headers. Do NOT skip the ## prefix.

Every bullet point MUST end with a cost in parentheses — a single dollar amount, e.g. ($25), ($0), (free). Never a range. No exceptions."""

    messages = [
        {"role": "system", "content": TRAVEL_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    async def generate():
        async with httpx.AsyncClient(timeout=90.0) as client:
            async with client.stream(
                "POST",
                TOGETHER_API_URL,
                headers={
                    "Authorization": f"Bearer {TOGETHER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": MODEL,
                    "messages": messages,
                    "max_tokens": 4000,
                    "temperature": 0.7,
                    "stream": True,
                },
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            yield "data: [DONE]\n\n"
                            return
                        try:
                            chunk = json.loads(data)
                            delta = chunk["choices"][0]["delta"]
                            if delta.get("content"):
                                payload = json.dumps({"content": delta["content"]})
                                yield f"data: {payload}\n\n"
                        except Exception:
                            pass

    return StreamingResponse(generate(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
