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

When you have enough information, generate a rich day-by-day itinerary that includes:
- 🏨 Accommodation recommendations (with price range)
- 🗺️ Day-by-day activities with timing
- 🍽️ Dining recommendations (breakfast, lunch, dinner) with local specialties
- 🚌 Transportation tips (getting around, airport transfers)
- 💰 Rough budget breakdown
- 💡 Insider tips and cultural notes
- ⚠️ Things to avoid or watch out for

Format your responses clearly with headers, bullet points, and emojis. Be specific — include real place names, neighborhoods, and practical advice. Make the user feel genuinely excited about their trip."""


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
    prompt = f"""Please create a comprehensive travel itinerary with the following details:

**Destination:** {request.destination}
**Travel Dates:** {request.start_date} to {request.end_date}
**Number of Travelers:** {request.travelers}
**Budget Level:** {request.budget}
**Interests:** {interests_str}
**Special Requests:** {request.special_requests or "None"}

Generate a full day-by-day itinerary with accommodations, activities, dining, transportation, and a budget breakdown."""

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
