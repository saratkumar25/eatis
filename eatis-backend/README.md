# EATIS — AI-Powered Event Traffic Intelligence System

Backend API for predicting and managing traffic congestion caused by public
events (festivals, rallies, sports matches, construction, parades, etc.).
Built for a hackathon MVP, following the supplied PRD and system architecture.

## What it does

Given an event (location, type, crowd size, timing), the system:

1. Predicts congestion severity, risk score, expected delay, and impact radius using an **XGBoost** model.
2. Generates **heatmap data** (lat/lng/intensity points) for a React + Leaflet frontend.
3. Recommends **resource allocation** — officers, barricades, patrol vehicles, emergency units.
4. Generates **alternate route / diversion** suggestions using a **NetworkX** road-graph model.
5. Lets operators ask a **Gemini 2.5 Flash**-powered AI Copilot natural-language questions about the event.
6. Exposes **analytics** (congestion distribution, high-risk zones, trends).
7. Supports **post-event analysis** — compare predicted vs. actual impact, track model accuracy.

## Tech stack

| Layer | Technology |
|---|---|
| API framework | FastAPI |
| Database | PostgreSQL + SQLAlchemy 2.0 (Alembic migrations) |
| ML | XGBoost, scikit-learn, pandas, numpy |
| Generative AI | Gemini 2.5 Flash (`google-generativeai`) |
| Routing | NetworkX (synthetic road graph; swap for OSM/GraphHopper in production) |
| Auth | JWT (python-jose) + bcrypt password hashing |
| Deployment | Docker / docker-compose |

## Project structure

```
eatis-backend/
├── app/
│   ├── main.py                 # FastAPI app factory + startup lifecycle
│   ├── config.py                # Settings (env vars)
│   ├── database.py              # SQLAlchemy engine/session
│   ├── core/
│   │   ├── security.py          # JWT + password hashing
│   │   └── dependencies.py      # get_current_user, role guards
│   ├── models/                  # SQLAlchemy ORM models
│   ├── schemas/                 # Pydantic request/response schemas
│   ├── ml/
│   │   ├── features.py          # Feature engineering
│   │   ├── trainer.py           # XGBoost training (+ synthetic data gen)
│   │   └── predictor.py         # Inference singleton
│   ├── services/                # Business logic (one file per domain)
│   └── routers/                 # FastAPI route handlers
├── scripts/
│   ├── train_model.py           # Standalone CLI to (re)train models
│   ├── seed_demo_data.py        # Populate sample events for demos
│   └── init_db.sql              # Postgres bootstrap (extensions)
├── alembic/                     # DB migrations
├── tests/                       # Pytest suite (SQLite-backed unit tests)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Quick start (Docker — recommended)

```bash
cp .env.example .env
# Edit .env and set GEMINI_API_KEY (get one free at https://aistudio.google.com/app/apikey)

docker compose up --build
```

The API will be available at `http://localhost:8000`. Interactive docs at
`http://localhost:8000/docs`. On first boot the backend automatically:
- creates all database tables,
- seeds a default admin user (`ADMIN_EMAIL` / `ADMIN_PASSWORD` from `.env`),
- trains the XGBoost models on a synthetic dataset (since no historical
  dataset ships with the repo) and caches them to the `models/` volume.

To also load demo events for a frontend walkthrough:

```bash
docker compose exec api python scripts/seed_demo_data.py
```

## Quick start (local, no Docker)

Requires Python 3.12 and a running PostgreSQL instance.

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# set DATABASE_URL to your local Postgres, set GEMINI_API_KEY

uvicorn app.main:app --reload
```

## Authentication

JWT bearer tokens. Roles: `admin`, `operator`, `analyst`, `viewer`.

```bash
# Register
curl -X POST localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Officer Singh","email":"singh@traffic.gov","password":"SecurePass123","role":"operator"}'

# Login
curl -X POST localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"singh@traffic.gov","password":"SecurePass123"}'
# → { "access_token": "...", "token_type": "bearer", ... }

# Use the token
curl localhost:8000/api/v1/events -H "Authorization: Bearer <token>"
```

A default admin account is also seeded on startup (`ADMIN_EMAIL` /
`ADMIN_PASSWORD` in `.env`, defaults to `admin@eatis.gov` / `Admin@123` —
**change this before any real deployment**).

## Core API endpoints

All routes are prefixed with `/api/v1`.

| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Create a user account |
| POST | `/auth/login` | Get a JWT access token |
| GET | `/auth/me` | Current user profile |
| POST | `/events` | Create an event — auto-runs prediction, resources, routes |
| GET | `/events` | List events (paginated, filterable) |
| GET | `/events/{id}` | Get event details |
| PATCH | `/events/{id}` | Update an event |
| DELETE | `/events/{id}` | Delete an event (admin only) |
| POST | `/events/simulate` | Simulate an event without persisting it |
| GET / POST | `/events/{id}/prediction`, `/predict` | Congestion prediction |
| GET / POST | `/events/{id}/resources`, `/resources/allocate` | Resource recommendations |
| GET / POST | `/events/{id}/routes`, `/routes/generate` | Diversion routes |
| GET | `/heatmap/{event_id}` | Leaflet-ready heatmap points |
| POST | `/copilot/ask` | Ask the Gemini AI Copilot a question |
| GET | `/copilot/history` | Past Copilot queries |
| GET | `/analytics/dashboard` | Aggregated analytics |
| POST / GET | `/post-event/{event_id}` | Submit / retrieve post-event analysis |

Full interactive documentation (request/response schemas, try-it-out) is
available at `/docs` (Swagger UI) and `/redoc`.

### Example: end-to-end event creation

```bash
curl -X POST localhost:8000/api/v1/events \
  -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -d '{
    "name": "Independence Day Rally",
    "event_type": "political_rally",
    "location_name": "Central Plaza",
    "latitude": 28.6139, "longitude": 77.2090,
    "start_datetime": "2026-08-15T09:00:00Z",
    "end_datetime": "2026-08-15T13:00:00Z",
    "expected_crowd_size": 10000,
    "has_road_closure": true,
    "road_closure_details": "Plaza approach roads closed 2 hrs prior"
  }'
```

Creating the event automatically triggers the XGBoost prediction, resource
allocation, and route-diversion pipeline — no extra calls needed before you
can fetch `/events/{id}/prediction`, `/events/{id}/resources`,
`/events/{id}/routes`, and `/heatmap/{id}`.

### Example: AI Copilot

```bash
curl -X POST localhost:8000/api/v1/copilot/ask \
  -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -d '{"query": "What will be the impact of a political rally with 10,000 attendees?", "event_id": 1}'
```

The Copilot automatically pulls the event's prediction and resource data
into its context when `event_id` is supplied, so its answer is grounded in
the actual model output rather than a generic response.

## Machine learning notes

No historical event dataset ships with this hackathon MVP, so
`app/ml/trainer.py` generates a **realistic synthetic dataset** (5,000
samples by default) using domain-informed heuristics (event-type risk
profiles, crowd-size scaling, weekend/peak-hour effects, road-closure
penalties) and trains four models on it:

- An `XGBClassifier` for the 4-class congestion level (low/medium/high/critical).
- Three `XGBRegressor`s for risk score, delay time, and impact radius.

This keeps the system fully functional out of the box. When real
historical event outcomes accumulate (via the post-event analysis
endpoint), swap `generate_synthetic_dataset()` for a query against the
`post_event_analysis` table and retrain with `scripts/train_model.py`.

Retrain manually:
```bash
python scripts/train_model.py --samples 10000
```
Or set `MODEL_RETRAIN_ON_STARTUP=true` in `.env` to retrain on every boot.

## Database migrations

The app auto-creates tables on startup for hackathon convenience. For
production-style schema evolution, use Alembic:

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## Testing

```bash
pip install -r requirements.txt
pytest
```

Unit tests run against an in-memory SQLite database (fast, no Postgres
required) and cover authentication, the full event → prediction →
resources → routes → heatmap pipeline, and input validation. The first
test run will train the XGBoost models if no cached model is found in
`models/`, which adds ~10–20 seconds one time only.

## Security

- Passwords hashed with bcrypt.
- JWT bearer tokens (HS256), configurable expiry.
- Role-based access control (`admin` / `operator` / `analyst` / `viewer`) enforced via FastAPI dependencies.
- Pydantic validation on every request body (lat/lng bounds, crowd-size bounds, password strength, date ordering, etc.).
- `GEMINI_API_KEY` and `SECRET_KEY` read only from environment variables, never hard-coded.
- CORS origins restricted via `CORS_ORIGINS` env var.
- Non-root Docker user.

Before any real deployment: rotate `SECRET_KEY`, change the seeded admin
password, and restrict `CORS_ORIGINS` to your actual frontend domain.

## Known limitations (hackathon scope)

- The road network for route diversions is a small synthetic graph
  centred on the event coordinates, not real OpenStreetMap data — swap in
  `osmnx` + a real OSM extract for production routing.
- The XGBoost model is trained on synthetic data; accuracy will improve
  once real post-event ground truth accumulates.
- Heatmap points are generated via Gaussian decay from the event
  epicentre rather than true road-segment-level congestion modelling.
