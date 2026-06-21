import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useQueries, useQuery } from "@tanstack/react-query";
import { useState, useMemo } from "react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/AppShell";
import { Card } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { MapView } from "@/components/MapView";
import { SeverityChip, severityHex } from "@/components/SeverityChip";
import type { EventItem, HeatmapResponse, Prediction, PaginatedEvents } from "@/lib/types";

export const Route = createFileRoute("/_app/map")({
  component: CityMap,
});

function CityMap() {
  const nav = useNavigate();
  const [visible, setVisible] = useState<Record<number, boolean>>({});

  const active = useQuery({
    queryKey: ["events", { status: "active" }],
    queryFn: async () =>
      (await api.get<PaginatedEvents>("/events", { params: { status: "active", limit: 100 } })).data,
  });
  const scheduled = useQuery({
    queryKey: ["events", { status: "scheduled" }],
    queryFn: async () =>
      (await api.get<PaginatedEvents>("/events", { params: { status: "scheduled", limit: 100 } })).data,
  });

  // Backend returns { total, skip, limit, data: [...] }
  const events: EventItem[] = useMemo(() => {
    const toArr = (d: PaginatedEvents | undefined): EventItem[] => d?.data ?? [];
    return [...toArr(active.data), ...toArr(scheduled.data)];
  }, [active.data, scheduled.data]);

  const heatmaps = useQueries({
    queries: events.map((e) => ({
      queryKey: ["heatmap", String(e.id)],
      queryFn: async () => (await api.get<HeatmapResponse>(`/heatmap/${e.id}`)).data,
      enabled: !!visible[e.id],
      retry: false,
    })),
  });

  const predictions = useQueries({
    queries: events.map((e) => ({
      queryKey: ["event", String(e.id), "prediction"],
      queryFn: async () => (await api.get<Prediction>(`/events/${e.id}/prediction`)).data,
      retry: false,
    })),
  });

  // Always default to Bangalore city center — events are still pinned on top
  const BANGALORE: [number, number] = [12.9716, 77.5946];
  const center: [number, number] = BANGALORE;

  const markers = events.map((e, i) => {
    const pred = predictions[i]?.data;
    const color = severityHex[pred?.congestion_level ?? "medium"];
    return {
      lat: e.latitude,
      lng: e.longitude,
      color,
      label: e.name,
      onClick: () => nav({ to: "/events/$id", params: { id: String(e.id) } }),
    };
  });

  const heatPoints = heatmaps.flatMap((q) => q.data?.points ?? []);

  return (
    <div className="p-6 lg:p-8">
      <PageHeader title="City-Wide Map" subtitle={`${events.length} active/upcoming events`} />
      <div className="grid lg:grid-cols-[1fr_300px] gap-4">
        <Card className="p-3">
          <MapView center={center} zoom={11} markers={markers} heatPoints={heatPoints} height="min(calc(100dvh - 280px), 600px)" />
        </Card>
        <Card className="p-4 lg:max-h-[calc(100dvh-220px)] lg:overflow-y-auto max-h-64 overflow-y-auto">
          <div className="display uppercase text-xs tracking-widest text-muted-foreground mb-3">
            Events
          </div>
          <ul className="space-y-2">
            {events.map((e, i) => {
              const pred = predictions[i]?.data;
              return (
                <li key={e.id} className="border border-border rounded-md p-2">
                  <div className="flex items-center gap-2 mb-1">
                    <Checkbox
                      checked={!!visible[e.id]}
                      onCheckedChange={(v) =>
                        setVisible((p) => ({ ...p, [e.id]: !!v }))
                      }
                      id={`v-${e.id}`}
                    />
                    <label
                      htmlFor={`v-${e.id}`}
                      className="text-sm flex-1 cursor-pointer truncate"
                    >
                      {e.name}
                    </label>
                    {pred && <SeverityChip level={pred.congestion_level} />}
                  </div>
                  <div className="text-[10px] mono text-muted-foreground">
                    {e.location_name}
                  </div>
                </li>
              );
            })}
            {events.length === 0 && !active.isLoading && !scheduled.isLoading && (
              <li className="text-sm text-muted-foreground p-2">No active or upcoming events.</li>
            )}
          </ul>
        </Card>
      </div>
    </div>
  );
}
