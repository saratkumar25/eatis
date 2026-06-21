# EATIS - Event Traffic Intelligence System

**Predict. Plan. Prevent Traffic Congestion Before It Happens.**

EATIS (Event Traffic Intelligence System) is an AI-powered traffic management platform designed to help traffic authorities predict and manage congestion caused by public events such as festivals, political rallies, sports events, construction activities, and public gatherings.

Using **Machine Learning (XGBoost)**, **Geospatial Analysis**, and **Gemini AI**, EATIS predicts traffic impact, generates congestion heatmaps, recommends resource deployment, suggests diversion routes, and provides AI-powered decision support.

---

## Key Features

### Event Management

* Create and manage event records
* Track event location, duration, crowd size, and road closures

### Traffic Prediction Engine

* XGBoost-based congestion prediction
* Predicts:

  * Congestion Severity
  * Risk Score
  * Delay Time
  * Impact Radius

### Congestion Heatmaps

* Predictive traffic heatmaps
* High-risk zone identification
* Impact radius visualization

### Resource Allocation Engine

Automatically recommends:

* Traffic Officers
* Barricades
* Patrol Vehicles
* Emergency Units

### Route Diversion Engine

* Alternative route recommendations
* Road closure planning
* Emergency corridor suggestions

### Event Simulator

Simulate future events and analyze:

* Traffic impact
* Congestion levels
* Resource requirements
* Diversion plans

### Gemini AI Traffic Copilot

* Natural language traffic queries
* Event impact explanations
* Resource recommendations
* Traffic reports and insights

### Analytics & Reporting

* Event statistics
* Congestion trends
* Resource utilization metrics
* Post-event analysis

---

## Technology Stack

### Backend

* FastAPI
* PostgreSQL
* SQLAlchemy
* XGBoost
* Scikit-Learn
* Pandas
* NumPy
* Gemini 2.5 Flash API

### Frontend

* React
* Vite
* Tailwind CSS
* TanStack Query
* TanStack Router
* Leaflet Maps

### Infrastructure

* Docker
* Docker Compose

### Mapping & Routing

* OpenStreetMap
* Leaflet
* NetworkX

---

## 🏛️ System Architecture

```text
React Dashboard
        │
        ▼
    FastAPI API
        │
 ┌──────┼────────────┬────────────┐
 ▼      ▼            ▼            ▼

Event  XGBoost    Route       Gemini
Module Prediction Engine     Copilot

 ▼      ▼            ▼            ▼

Events Heatmaps Diversions Reports

        │
        ▼

    PostgreSQL
```

---

## Getting Started

### Backend

```bash
cd eatis-backend
cp .env.example .env
```

Add your Gemini API Key:

```env
GEMINI_API_KEY=your_api_key
```

Start services:

```bash
docker compose up --build -d
```

Backend API:

```text
http://localhost:8001
```

Swagger Documentation:

```text
http://localhost:8001/docs
```

---

### Frontend

```bash
cd eatis-frontend/eatis-dispatch
npm install
npm run dev
```

Frontend URL:

```text
http://localhost:5173
```

---

## Default Credentials

```text
Email: admin@eatis.gov
Password: Admin@123
```

---

## Project Structure

```text
eatis/
├── eatis-backend/
│   ├── app/
│   ├── scripts/
│   ├── tests/
│   ├── alembic/
│   └── docker-compose.yml
│
└── eatis-frontend/
    └── eatis-dispatch/
```

---

## Expected Impact

* Reduced Traffic Congestion
* Faster Decision Making
* Improved Resource Utilization
* Better Event Preparedness
* Enhanced Emergency Response
* Data-Driven Traffic Operations

---

## Future Enhancements

* Live GPS Integration
* CCTV Analytics
* Crowd Density Estimation
* Weather Impact Prediction
* Smart Signal Optimization
* Multi-Event Prediction
* AI Incident Response Assistant

---    

## Team

**T's Team**

Building smarter traffic management through AI-driven operational intelligence.
