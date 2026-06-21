"""
app/services/route_service.py
──────────────────────────────
Route diversion recommendation engine.

Uses NetworkX to model a simplified road graph centred on the event
location.  In production this would be replaced by OpenStreetMap /
GraphHopper data.  The synthetic graph still produces realistic
GeoJSON polylines that Leaflet can render directly.
"""

from __future__ import annotations

import json
import math
import random
from typing import Optional

import networkx as nx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.prediction import Prediction
from app.models.route import Route, RouteType

# ── Geometry helpers ───────────────────────────────────────────────────────────

def _offset(lat: float, lon: float, d_lat_km: float, d_lon_km: float) -> tuple[float, float]:
    dlat = d_lat_km / 111.0
    dlon = d_lon_km / (111.0 * math.cos(math.radians(lat)))
    return round(lat + dlat, 6), round(lon + dlon, 6)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dl / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _build_road_graph(lat: float, lon: float, radius_km: float, seed: int) -> nx.Graph:
    """
    Build a small synthetic road network around (lat, lon).
    Nodes are distributed on a rough grid; edges model roads.
    """
    rng = random.Random(seed)
    G = nx.Graph()
    step = radius_km / 3.0
    offsets = [(-2, -2), (-2, 0), (-2, 2), (0, -2), (0, 2), (2, -2), (2, 0), (2, 2),
               (-1, -1), (-1, 1), (1, -1), (1, 1), (0, 0)]  # centre is blocked

    for i, (dy, dx) in enumerate(offsets):
        flat, flon = _offset(lat, lon, dy * step, dx * step)
        noise_lat = rng.uniform(-0.002, 0.002)
        noise_lon = rng.uniform(-0.002, 0.002)
        G.add_node(i, lat=flat + noise_lat, lon=flon + noise_lon)

    # Connect nearby nodes
    nodes = list(G.nodes(data=True))
    for i, (ni, di) in enumerate(nodes):
        for j, (nj, dj) in enumerate(nodes):
            if i >= j:
                continue
            dist = _haversine_km(di["lat"], di["lon"], dj["lat"], dj["lon"])
            if dist < step * 1.8:
                weight = dist * rng.uniform(0.8, 1.4)
                G.add_edge(ni, nj, weight=weight, dist_km=round(dist, 2))
    return G


def _path_to_geojson(G: nx.Graph, path: list[int]) -> str:
    coords = [[G.nodes[n]["lon"], G.nodes[n]["lat"]] for n in path]
    return json.dumps({
        "type": "LineString",
        "coordinates": coords,
    })


def _path_distance(G: nx.Graph, path: list[int]) -> float:
    total = 0.0
    for a, b in zip(path, path[1:]):
        total += G[a][b].get("dist_km", 0.0)
    return round(total, 2)


# ── Service function ───────────────────────────────────────────────────────────

_ROUTE_TEMPLATES = [
    {
        "route_type": RouteType.ALTERNATE,
        "name_tpl": "Northern Bypass via {loc}",
        "offset": (3.0, 0.0),
        "dest_offset": (0.0, 3.0),
        "benefit": "Avoids event epicentre; adds ~4 km but saves ~20 min",
    },
    {
        "route_type": RouteType.ALTERNATE,
        "name_tpl": "Southern Diversion via {loc}",
        "offset": (-3.0, 0.0),
        "dest_offset": (0.0, -3.0),
        "benefit": "Best for south-bound traffic; alternate highway access",
    },
    {
        "route_type": RouteType.EMERGENCY_ACCESS,
        "name_tpl": "Emergency Corridor {loc}",
        "offset": (1.5, 1.5),
        "dest_offset": (-1.5, -1.5),
        "benefit": "Reserved lane for emergency vehicles; do not block",
    },
]


def generate_routes(event_id: int, db: Session) -> list[Route]:
    event: Optional[Event] = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    pred: Optional[Prediction] = db.query(Prediction).filter(Prediction.event_id == event_id).first()
    if not pred:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found. Run /predict first.",
        )

    # Delete existing routes for this event
    db.query(Route).filter(Route.event_id == event_id).delete()

    radius = max(pred.impact_radius_km, 2.0)   # ensure graph is always wide enough
    G = _build_road_graph(event.latitude, event.longitude, radius, seed=event_id)

    saved_routes: list[Route] = []
    nodes = list(G.nodes())

    for idx, tmpl in enumerate(_ROUTE_TEMPLATES):
        # Pick source and destination nodes based on offsets
        src_lat, src_lon = _offset(event.latitude, event.longitude, *tmpl["offset"])
        dst_lat, dst_lon = _offset(event.latitude, event.longitude, *tmpl["dest_offset"])

        # Find closest nodes in graph — guarantee src != dst
        src_node = min(nodes, key=lambda n: _haversine_km(
            src_lat, src_lon, G.nodes[n]["lat"], G.nodes[n]["lon"]))
        dst_candidates = [n for n in nodes if n != src_node]
        dst_node = min(dst_candidates, key=lambda n: _haversine_km(
            dst_lat, dst_lon, G.nodes[n]["lat"], G.nodes[n]["lon"]))

        try:
            path = nx.shortest_path(G, src_node, dst_node, weight="weight")
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            path = [src_node, dst_node]

        # Ensure we always have at least 2 points for a valid LineString
        if len(path) < 2:
            path = [src_node, dst_node]

        dist = _path_distance(G, path)
        speed_kmh = 40 if tmpl["route_type"] == RouteType.EMERGENCY_ACCESS else 30
        est_minutes = int((dist / speed_kmh) * 60) if dist > 0 else 5

        route = Route(
            event_id=event_id,
            route_type=tmpl["route_type"],
            route_name=tmpl["name_tpl"].format(loc=event.location_name),
            description=tmpl["benefit"],
            geojson_coordinates=_path_to_geojson(G, path),
            distance_km=dist,
            estimated_time_minutes=est_minutes,
            diversion_benefit=tmpl["benefit"],
        )
        db.add(route)
        saved_routes.append(route)

    db.commit()
    for r in saved_routes:
        db.refresh(r)
    return saved_routes


def get_routes(event_id: int, db: Session) -> list[Route]:
    return db.query(Route).filter(Route.event_id == event_id).all()
