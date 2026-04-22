# MP1 -- Atlas AI Travel Planner
## Prompt Archive
**CSC394/IS376 Senior Capstone | Prof. Clark Elliott**

---

## 1. Design Prompts

### 1.1 Initial Project Design
**Prompt used with Claude Code (AI collaborator):**
> "I need to build a travel planner mini project. It should allow users to plan a trip manually (fill out a form) but also integrate an LLM so users can just describe what they want and the AI will plan it for them. Use FastAPI/uvicorn for the backend, together.ai for the LLM. The design should be very professional AI-style, light red/rose color palette, and creative — not amateur."

**Purpose:** Establish overall architecture, feature set, and visual design direction.

---

### 1.2 UI/UX Design Decisions
**Prompt used with Claude Code:**
> "Very professional AI style! Light red and creative... not amateur."

**Purpose:** Define the design language — led to the rose/red color palette, glassmorphism nav, gradient hero, pill-style controls, and overall premium SaaS aesthetic.

---

### 1.3 Itinerary Output Redesign
**Prompt used with Claude Code:**
> "I'm not sure how I feel about it just returning text? Feel like that's not enjoyable, kinda bland."

**Purpose:** Redesign the itinerary output from plain rendered markdown into structured visual day cards with a destination banner, section badges, and hover effects. Led to the `formatItinerary()` function and `.day-card` layout.

---

### 1.4 Animated RGB Background with Grain
**Prompt used with Claude Code:**
> "Put some nice background effects on the front end, like a moving RGB background make it grain."

**Purpose:** Add animated color blob background (5 independently floating blobs with circular path keyframe animations) and a CSS SVG grain overlay for a premium textured feel.

---

### 1.5 Color Scheme Change to Green
**Prompt used with Claude Code:**
> "Make the RGB move around and actually make the main color green."

**Purpose:** Change the primary color from rose/red to green across all CSS variables, button gradients, badges, and UI elements. Also improved blob animations from bounce (alternate) to full circular looping paths for more dynamic movement.

---

### 1.6 Light Theme Restoration
**Prompt used with Claude Code:**
> "I don't want dark theme though."

**Purpose:** Remove the dark theme override block while keeping the animated RGB blob background. Converted blobs to pastel colors suitable for a light background.

---

## 2. Code Generation Prompts

### 2.1 FastAPI Backend
**Prompt used with Claude Code:**
> "Follow all of these rules and use FastAPI/uvicorn. I am going to make a travel planner."

**Purpose:** Generate the complete `main.py` server with `/api/chat/stream`, `/api/plan/manual`, Together.ai SSE streaming, Pydantic models, and python-dotenv.

---

### 2.2 AI System Prompt (Travel Assistant Persona)
**Prompt used with Claude Code:**
> Design an expert travel planning AI system prompt. The AI should be named Atlas, have a warm and enthusiastic personality, ask clarifying questions when input is vague, and generate rich day-by-day itineraries with accommodations, dining, transportation, budget breakdown, and insider tips.

**Purpose:** Create the `TRAVEL_SYSTEM_PROMPT` constant defining Atlas's behavior in `main.py`.

---

### 2.3 Frontend — Professional UI
**Prompt used with Claude Code:**
> Build a single-page HTML/CSS/JS frontend with sticky nav, hero section, manual planning form (destination, dates, traveler stepper, budget pills, interest tags, special requests), AI chat interface with streaming, typing indicator, suggestion chips, copy/print actions, and full mobile responsiveness.

**Purpose:** Generate the complete `static/index.html`.

---

### 2.4 Streaming SSE Implementation
**Prompt used with Claude Code:**
> Implement Server-Sent Events streaming on both the FastAPI backend and the JavaScript frontend. Backend forwards Together.ai stream chunks; frontend reads with ReadableStream, parses `data:` lines, renders tokens in real time.

**Purpose:** Enable live streaming AI responses for both modes.

---

### 2.5 Destination Autocomplete
**Prompt used with Claude Code:**
> "When typing in destinations, give suggestions."

**Purpose:** Add a `/api/suggestions` backend endpoint (proxying OpenStreetMap Nominatim) and a keyboard-navigable autocomplete dropdown in the frontend with debouncing, arrow key navigation, and click-to-select.

---

### 2.6 Empty Date Fields
**Prompt used with Claude Code:**
> "Have the date fields be empty."

**Purpose:** Remove the default date pre-fill logic so fields start blank.

---

### 2.7 Destination Input Width Fix
**Prompt used with Claude Code:**
> "You made the bar smaller for some reason? Put it back how it was."

**Purpose:** Fixed the autocomplete wrapper div breaking the flex-stretch of the destination input by adding `width: 100%` to `.autocomplete-wrap` and its child input.

---

### 2.8 Interactive Features — Map, Editable Itinerary, Weather, Budget, Save/Load
**Prompt used with Claude Code:**
> "What are some improvements we can make to rival top trip planning websites? I want more interactivity, maps? etc."
> (followed by) "Add all 12." → then narrowed to: "Just do what you think would be the most important."

**Purpose:** Add the top 5 most impactful interactive features:
1. **Leaflet.js map** — OpenStreetMap, destination pin, tab-switchable
2. **Editable itinerary** — click ✏️ to edit any activity inline, 🗑️ to delete
3. **Add custom activities** — `+ Add activity` per day card, auto-focus edit
4. **Weather per day** — Open-Meteo free API via `/api/weather`, weather badge on each day header
5. **Budget tracker** — `$` input per activity, rolling total in bottom bar
6. **Save/load trips** — localStorage with up to 10 trips, restore from `📂 My Trips`

Led to:
- New backend endpoints: `/api/geocode` (Nominatim), `/api/weather` (Open-Meteo)
- Complete restructure of result panel into tabbed trip container
- `buildTripFromText()` data model parser
- `renderTripUI()`, `renderDayCard()`, `renderActivity()` render functions
- Full CRUD for activities: `addActivity()`, `deleteActivity()`, `startEdit()`, `saveEdit()`
- `updateCost()`, `updateBudgetTotal()` for budget tracking
- `initMapWithCoords()` with Leaflet CDN
- `saveTrip()`, `restoreSavedTrip()`, `deleteSavedTrip()` for localStorage persistence
- `showToast()` notification system
- Print function updated for structured itinerary output

---

### 2.9 Encoding / Windows Compatibility Fix
**Prompt used with Claude Code:**
> "there is an encoding error in here right? and it wont work on windws?"

**Purpose:** Identified that `open("static/index.html")` in the root route lacked encoding specification, which breaks on Windows (default cp1252). Fix replaced the manual file read with FastAPI's `FileResponse`.

---

**Prompt used with Claude Code:**
> "isnt there a better way to fix this? doesnt fastapi handle this?"

**Purpose:** Switched from `open()` with `encoding="utf-8"` to `FileResponse("static/index.html")`, which is the idiomatic FastAPI approach — handles encoding, headers, and caching automatically.

---

**Prompt used with Claude Code:**
> "yes"

**Purpose:** Confirmed the `FileResponse` fix. Updated import to remove unused `HTMLResponse` and add `FileResponse`.

---

**Prompt used with Claude Code:**
> "update the prompt log to refelect everything i said unchanged. exactly how it is. and every prompt i make now add it to the prompt exactly as is"

**Purpose:** Establish ongoing requirement to log every user prompt verbatim and in full to `prompts/prompts_archive.md`.

---

**Prompt used with Claude Code:**
> "you forgot the last prompt i made."

**Purpose:** Flagged that the "update the prompt log" prompt was missing from the archive.

---

**Prompt used with Claude Code:**
> "i just said to update the prompt log for EVERY SINGLE PROMPT I MAKE"

**Purpose:** Reinforced that every prompt, including meta/conversational ones, must be logged verbatim immediately.

---

**Prompt used with Claude Code:**
> "can i use react for the frontend. It will give it more organization and a modern framework."

**Purpose:** Evaluating whether to migrate the frontend from a single `index.html` to a React app.

---

**Prompt used with Claude Code:**
> "No not yet. has everything been fixed (cross-platform problems, bugs, etc)"

**Purpose:** Audit the project for remaining cross-platform issues or bugs before further development.

---

**Prompt used with Claude Code:**
> "commit the cross-platform fix and add what you did in the message keep it short though"

**Purpose:** Commit the `FileResponse` cross-platform fix with a brief descriptive commit message.

---

**Prompt used with Claude Code:**
> "now fix the remaining bugs and commit"

**Purpose:** Fix the two remaining bugs: `mapInstance` not destroyed before re-initialization, and deprecated `weathercode` → `weather_code` Open-Meteo API field.

---

**Prompt used with Claude Code:**
> "explain to me what was fixed and what the problem was"

**Purpose:** Understand the two bugs that were fixed — the Open-Meteo API deprecation and the Leaflet map memory leak.

---

**Prompt used with Claude Code:**
> "make sure everything is good, stage commit and push. do not push anything that should not be pushed"

**Purpose:** Final review, stage all safe files, commit, and push to remote.

---

## 3. Documentation Prompts

### 3.1 Prompt Archive
**Prompt used with Claude Code:**
> "You have logged all prompts and followed all directions from the instructions correct?"

**Purpose:** Audit compliance with assignment requirements and update this archive with all prompts from the full development session.

---

## 4. How AI Was Used in This Project

### Design
Claude Code collaboratively designed the full application architecture — the two-mode approach (Manual + AI Chat), client/server split (FastAPI + browser), LLM integration strategy (Together.ai streaming), visual design language (green palette, animated blob background, grain texture, glassmorphism), and all iterative UI improvements based on feedback.

### Code
Claude Code generated approximately 95%+ of the code across all files:
- `main.py` — FastAPI server with SSE streaming, Together.ai integration, Nominatim geocoding, Open-Meteo weather, autocomplete suggestions
- `static/index.html` — Complete single-page frontend (HTML, CSS, JS) including all interactive features
- `requirements.txt` — Dependency list
- `prompts/prompts_archive.md` — This file

### Documentation
Claude Code generated this prompts archive in full, updated it across multiple sessions, and drafted all documentation content.

---

## 5. Assignment Requirements Checklist

| Requirement | Status | Notes |
|---|---|---|
| Labeled "MP1 -- Atlas AI Travel Planner" | ✅ | In `main.py` title, nav, and footer |
| Client/server with browser as client | ✅ | FastAPI backend + HTML/JS frontend |
| FastAPI / uvicorn | ✅ | `main.py` with uvicorn |
| LLM integration (realtime calls) | ✅ | Together.ai `meta-llama/Llama-3.3-70B-Instruct-Turbo` |
| Accepts user input in browser | ✅ | Manual form + AI chat |
| Processes data on server | ✅ | All AI calls proxied through FastAPI |
| Built using AI collaboration tools | ✅ | Claude Code (Anthropic) throughout |
| Documented using AI collaborator | ✅ | This file |
| Labeled section in Project Manual | ✅ | Added as `PROJECT_MANUAL_MP1_SECTION.md` |
| Prompts archived electronically | ✅ | `prompts/prompts_archive.md` |
| Prompts in formal documentation | ✅ | Included in `PROJECT_MANUAL_MP1_SECTION.md` with archive reference |

---

## 6. Project File Structure

```
MiniProject_TravelPlanner/
├── main.py                  # FastAPI backend server
├── requirements.txt         # Python dependencies
├── .env                     # API key (not committed to version control)
├── static/
│   └── index.html           # Single-page frontend application
└── prompts/
    └── prompts_archive.md   # This file — all archived prompts
```

## 7. Running the Project

```bash
# 1. Install dependencies (requires uv)
uv pip install -r requirements.txt

# 2. Set your Together.ai API key in .env
#    TOGETHER_API_KEY=your_key_here

# 3. Start the server (uvicorn)
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 4. Open browser at http://localhost:8000
```
