# EATIS - Event Traffic Intelligence System

**Predict. Plan. Prevent Traffic Congestion Before It Happens.**

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-Frontend-61DAFB?logo=react&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-ML%20Model-AA0000)
![Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-4285F4?logo=googlegemini&logoColor=white)
![Status](https://img.shields.io/badge/status-active-success)

EATIS is an AI-powered traffic management platform that helps traffic authorities predict and manage congestion caused by public events — festivals, rallies, sports events, construction, and large gatherings — using **XGBoost**, **geospatial analysis**, and **Gemini AI**.
 
🔗 **Live Demo:** [eatis.vercel.app](https://eatis.vercel.app)

---

## How to Use
 
Once you're logged into the dashboard, here's the typical workflow:
 
1. **Create an event**
   Go to **Events → New Event** and fill in the location, expected crowd size, duration, and any planned road closures. This is the only manual input the system needs — everything else is generated from it.
2. **Check the traffic prediction**
   Open the event's detail page to see the model's output: predicted **congestion severity**, **risk score**, **delay time**, and **impact radius**.
3. **View the heatmap**
   Switch to the **Map / Heatmap** view to see the predicted congestion overlaid on the area around the event, including high-risk zones.
4. **Review resource recommendations**
   The **Resources** tab shows the suggested number of traffic officers, barricades, patrol vehicles, and emergency units for the event.
5. **Check suggested diversions**
   The **Diversions** tab lists alternative routes, road-closure suggestions, and emergency corridors to plan around the predicted impact.
6. **Run a simulation (optional)**
   Use the **Event Simulator** to test a hypothetical event before it's confirmed — adjust crowd size or location and see how the prediction changes.
7. **Ask the AI Copilot**
   Use the chat panel to ask plain-language questions, e.g. *"Which roads are highest risk for Saturday's event?"* or *"Summarize this week's traffic reports."*
8. **Check analytics**
   The **Analytics** section tracks event statistics, congestion trends, resource utilization, and post-event analysis over time.
---
 
## Key Features
 
- **Event Management** — create and track events, locations, crowd size, and road closures
- **Traffic Prediction Engine** — XGBoost model for congestion severity, risk score, delay time, impact radius
- **Congestion Heatmaps** — predictive heatmaps and high-risk zone visualization
- **Resource Allocation Engine** — recommends officers, barricades, patrol vehicles, emergency units
- **Route Diversion Engine** — alternative routes, closure planning, emergency corridors
- **Event Simulator** — test hypothetical events before committing to a plan
- **Gemini AI Traffic Copilot** — natural-language querying, explanations, and reports
- **Analytics & Reporting** — trends, utilization metrics, post-event analysis
---

## Tech Stack
 
| Layer | Technologies |
|---|---|
| **Backend** | FastAPI, PostgreSQL, SQLAlchemy, XGBoost, Scikit-Learn, Pandas, NumPy, Gemini 2.5 Flash API |
| **Frontend** | React, Vite, Tailwind CSS, TanStack Query, TanStack Router, Leaflet Maps |
| **Infrastructure** | Docker, Docker Compose |
| **Mapping & Routing** | OpenStreetMap, Leaflet, NetworkX |

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

## Default Credentials

### Operator role:
```text
Email: operator1@gmail.com
Password: operator123
```
### Analyst role:
```text
Email: analyst1@gmail.com
Password: operator123
```
### Viewer role:
```text
Email: viewer1@gmail.com
Password: operator123
```

Local development only — change these (or remove the seed) before deploying anywhere publicly reachable.

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
* Advanced Role-Based Access
---    

## Team

**T's Team**

Building smarter traffic management through AI-driven operational intelligence.
