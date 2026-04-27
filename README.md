# Atlas AI Travel Planner

Atlas AI Travel Planner is a FastAPI-based travel planning app with a static web UI.  
It helps users generate day-by-day travel itineraries using Together AI, with built-in destination suggestions and weather forecasting.

## Features

- AI-powered travel chat with streaming responses
- Manual itinerary generation from structured trip details
- Destination suggestions using OpenStreetMap Nominatim
- Geocoding support for map and location features
- 16-day weather forecast using Open-Meteo
- Simple static frontend served by FastAPI

## Tech Stack

- Python
- FastAPI
- Uvicorn
- HTTPX
- python-dotenv
- Together AI API

## Project Structure

- `main.py` - FastAPI app and API routes
- `static/index.html` - Frontend interface
- `requirements.txt` - Python dependencies

## Prerequisites

- Python 3.10+ recommended
- A Together AI API key

## Setup

1. Clone the repository and move into the project folder.
2. Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root:

```env
TOGETHER_API_KEY=your_api_key_here
```

## Run the App

Start the FastAPI development server:

```bash
python main.py
```

The app will run at:

- [http://localhost:8000](http://localhost:8000)

## API Endpoints

- `GET /` - Serves the frontend
- `GET /api/suggestions?q=...` - Destination suggestions
- `GET /api/geocode?q=...` - Geocode a destination to lat/lon
- `GET /api/weather?destination=...` - Weather forecast and coordinates
- `POST /api/chat/stream` - Streaming travel chat response
- `POST /api/plan/manual` - Structured itinerary generation

## Notes

- If `TOGETHER_API_KEY` is missing, AI chat and manual itinerary endpoints will return an error.
- The app uses external APIs (Together AI, Nominatim, Open-Meteo), so internet access is required.

