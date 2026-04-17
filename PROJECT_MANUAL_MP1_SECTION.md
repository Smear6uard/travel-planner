# MP1 -- Atlas AI Travel Planner (Project Manual Section)

## Project Label
**MP1 -- Atlas AI Travel Planner**

## Overview
This mini project is a client/server travel-planning web app. The browser client allows users to either:
1. enter trip details manually, or
2. chat with an AI assistant to generate an itinerary.

The backend is implemented with FastAPI and served with uvicorn.

## Assignment Rule Compliance

### 1) Domain and AI Collaboration
- Domain is travel planning (no domain constraints).
- The project was designed, coded, and documented with AI collaboration.

### 2) Client/Server Architecture
- Browser client: single-page app in `static/index.html`.
- Server: FastAPI app in `main.py`.
- Local deployment preserves web-style architecture and is directly extensible.

### 3) FastAPI / uvicorn
- FastAPI is used for API routes and serving the web app.
- uvicorn is used to run the ASGI app.
- Run command:
  - `uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload`

### 4) LLM Integration (Preferred)
- Real-time LLM calls are integrated through Together AI (`/api/chat/stream` and `/api/plan/manual`).
- Streaming response tokens are forwarded to the browser using Server-Sent Events.

### 5) User Input and Server Processing
- User inputs are collected in the browser (forms and chat).
- Input is processed on the server (validation, API calls, itinerary generation, weather/geocoding lookups).

### 6) Documentation and Prompt Archiving
- Prompt archive is stored electronically in `prompts/prompts_archive.md`.
- This file provides a labeled project-manual section for MP1.
- It also documents how AI was used for:
  - design,
  - code generation,
  - documentation.

## How AI Was Used
- **Design:** architecture, UI/UX direction, interaction patterns.
- **Code:** backend endpoints, streaming logic, frontend interactivity.
- **Documentation:** prompt archive and compliance checklist.

## Files for Evidence
- `main.py`
- `static/index.html`
- `requirements.txt`
- `prompts/prompts_archive.md`
- `PROJECT_MANUAL_MP1_SECTION.md`
