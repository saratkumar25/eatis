import { lazy, Suspense } from "react";
import type { HeatmapPoint } from "@/lib/types";

const MapInner = lazy(() => import("./MapInner"));

export interface MapMarker {
  lat: number;
  lng: number;
  color?: string;
  label?: string;
  onClick?: () => void;
}

export interface MapPolyline {
  coords: [number, number][];
  color?: string;
  label?: string;
}

interface Props {
  center: [number, number];
  zoom?: number;
  markers?: MapMarker[];
  heatPoints?: HeatmapPoint[];
  polylines?: MapPolyline[];
  height?: string;
}

export function MapView(props: Props) {
  // Don't render the map if center coords are invalid
  const lat = Number(props.center?.[0]);
  const lng = Number(props.center?.[1]);
  if (isNaN(lat) || isNaN(lng)) {
    return (
      <div
        style={{ height: props.height ?? "400px" }}
        className="w-full rounded-md overflow-hidden border border-border bg-steel flex items-center justify-center text-sm text-muted-foreground"
      >
        No location data
      </div>
    );
  }

  return (
    <div
      style={{ height: props.height ?? "400px", isolation: "isolate", position: "relative" }}
      className="w-full rounded-md overflow-hidden border border-border bg-steel"
    >
      <Suspense
        fallback={
          <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
            Loading map…
          </div>
        }
      >
        <MapInner {...props} />
      </Suspense>
    </div>
  );
}
