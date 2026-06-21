import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.heat";
import type { HeatmapPoint } from "@/lib/types";
import type { MapMarker, MapPolyline } from "./MapView";

interface Props {
  center: [number, number];
  zoom?: number;
  markers?: MapMarker[];
  heatPoints?: HeatmapPoint[];
  polylines?: MapPolyline[];
}

// Fix default icon paths (CDN fallback)
const DefaultIcon = L.icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});
L.Marker.prototype.options.icon = DefaultIcon;

/** Ensure we always have a valid [lat, lng] pair — falls back to London if invalid. */
function safeCenter(c: [number, number]): [number, number] {
  const lat = Number(c?.[0]);
  const lng = Number(c?.[1]);
  if (isNaN(lat) || isNaN(lng)) return [51.505, -0.09];
  return [lat, lng];
}

export default function MapInner({
  center,
  zoom = 13,
  markers = [],
  heatPoints = [],
  polylines = [],
}: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const validCenter = safeCenter(center);

  useEffect(() => {
    if (!ref.current || mapRef.current) return;
    const map = L.map(ref.current, { center: validCenter, zoom, zoomControl: true });
    // Standard OpenStreetMap tiles (colorful road map style)
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors",
      maxZoom: 19,
    }).addTo(map);
    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    map.setView(safeCenter(center), zoom);
  }, [center, zoom]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const layers: L.Layer[] = [];

    markers.forEach((m) => {
      // Skip markers with invalid coordinates
      const lat = Number(m.lat);
      const lng = Number(m.lng);
      if (isNaN(lat) || isNaN(lng)) return;

      const icon = m.color
        ? L.divIcon({
            className: "custom-marker",
            html: `<div style="background:${m.color};width:18px;height:18px;border-radius:50%;border:2px solid #fff;box-shadow:0 0 0 2px rgba(0,0,0,0.4)"></div>`,
            iconSize: [18, 18],
            iconAnchor: [9, 9],
          })
        : DefaultIcon;
      const marker = L.marker([lat, lng], { icon });
      if (m.label) marker.bindPopup(m.label);
      if (m.onClick) marker.on("click", m.onClick);
      marker.addTo(map);
      layers.push(marker);
    });

    polylines.forEach((p) => {
      // Guard: coords must be a real array; skip otherwise
      const rawCoords = Array.isArray(p.coords) ? p.coords : [];
      const validCoords = rawCoords.filter(
        (c) => Array.isArray(c) && !isNaN(Number(c[0])) && !isNaN(Number(c[1])),
      ) as [number, number][];
      if (validCoords.length < 2) return;

      const line = L.polyline(validCoords, {
        color: p.color ?? "#2D6CDF",
        weight: 4,
        opacity: 0.85,
      });
      if (p.label) line.bindPopup(p.label);
      line.addTo(map);
      layers.push(line);
    });

    const validHeatPoints = (heatPoints ?? []).filter(
      (p) => !isNaN(Number(p.lat)) && !isNaN(Number(p.lng)),
    );
    if (validHeatPoints.length > 0) {
      // @ts-expect-error leaflet.heat extends L
      const heat = L.heatLayer(
        validHeatPoints.map((p) => [p.lat, p.lng, p.intensity]),
        { radius: 25, blur: 20, maxZoom: 17 },
      );
      heat.addTo(map);
      layers.push(heat);
    }

    return () => {
      layers.forEach((l) => map.removeLayer(l));
    };
  }, [markers, heatPoints, polylines]);

  return <div ref={ref} className="h-full w-full" />;
}
