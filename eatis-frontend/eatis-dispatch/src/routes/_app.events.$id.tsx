import { createFileRoute, Link, useNavigate, Outlet, useRouterState } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/AppShell";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { SeverityChip, severityHex } from "@/components/SeverityChip";
import { MapView } from "@/components/MapView";
import type {
  EventItem,
  Prediction,
  ResourceAllocation,
  RouteSuggestion,
  HeatmapResponse,
  PostEventAnalysis,
} from "@/lib/types";
import { formatIST } from "@/lib/utils";
import {
  RefreshCw,
  Pencil,
  Bot,
  Trash2,
  Users,
  Construction,
  Car,
  Ambulance,
  Truck,
  ChevronDown,
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/lib/auth";
import { openCopilot } from "@/components/CopilotLauncher";
import { toast } from "sonner";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { PostEventForm, PostEventReport } from "@/components/PostEventViews";

export const Route = createFileRoute("/_app/events/$id")({
  component: CommandCenter,
});

function Panel({
  title,
  actions,
  children,
}: {
  title: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="display uppercase text-sm tracking-widest text-muted-foreground">
          {title}
        </h2>
        <div className="flex gap-2">{actions}</div>
      </div>
      {children}
    </Card>
  );
}

function Metric({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <div className="text-[10px] uppercase mono text-muted-foreground tracking-widest">
        {label}
      </div>
      <div className="mono text-lg mt-0.5">{value}</div>
    </div>
  );
}

/** Parse geojson_coordinates — backend stores it as a JSON string (raw array or GeoJSON object). */
function parseCoords(raw: string | null | undefined): [number, number][] {
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    // Raw array: [[lat, lng], ...]
    if (Array.isArray(parsed)) return parsed as [number, number][];
    // GeoJSON LineString: { type: "LineString", coordinates: [[lng, lat], ...] }
    if (parsed?.coordinates && Array.isArray(parsed.coordinates))
      return parsed.coordinates as [number, number][];
  } catch {
    // ignore malformed JSON
  }
  return [];
}

function CommandCenter() {
  const { id } = Route.useParams();
  const { can } = useAuth();
  const qc = useQueryClient();
  const nav = useNavigate();
  const isEdit = useRouterState({ select: (s) => s.location.pathname.endsWith("/edit") });

  const event = useQuery({
    queryKey: ["event", id],
    queryFn: async () => (await api.get<EventItem>(`/events/${id}`)).data,
  });

  if (isEdit) return <Outlet />;

  const prediction = useQuery({
    queryKey: ["event", id, "prediction"],
    queryFn: async () => (await api.get<Prediction>(`/events/${id}/prediction`)).data,
    retry: false,
  });

  const resources = useQuery({
    queryKey: ["event", id, "resources"],
    queryFn: async () => (await api.get<ResourceAllocation>(`/events/${id}/resources`)).data,
    retry: false,
  });

  const routes = useQuery({
    queryKey: ["event", id, "routes"],
    queryFn: async () => (await api.get<RouteSuggestion[]>(`/events/${id}/routes`)).data,
    retry: false,
  });

  const heatmap = useQuery({
    queryKey: ["heatmap", id],
    queryFn: async () => (await api.get<HeatmapResponse>(`/heatmap/${id}`)).data,
    retry: false,
  });

  const postEvent = useQuery({
    queryKey: ["post-event", id],
    queryFn: async () => (await api.get<PostEventAnalysis>(`/post-event/${id}`)).data,
    retry: false,
    enabled: event.data?.status === "completed",
  });

  const rerunPred = useMutation({
    mutationFn: async () => (await api.post(`/events/${id}/predict`)).data,
    onSuccess: () => {
      toast.success("Prediction recomputed");
      qc.invalidateQueries({ queryKey: ["event", id, "prediction"] });
      qc.invalidateQueries({ queryKey: ["heatmap", id] });
    },
  });

  const recompResources = useMutation({
    mutationFn: async () => (await api.post(`/events/${id}/resources/allocate`)).data,
    onSuccess: () => {
      toast.success("Resources recomputed");
      qc.invalidateQueries({ queryKey: ["event", id, "resources"] });
    },
  });

  const regenRoutes = useMutation({
    mutationFn: async () => (await api.post(`/events/${id}/routes/generate`)).data,
    onSuccess: () => {
      toast.success("Routes regenerated");
      qc.invalidateQueries({ queryKey: ["event", id, "routes"] });
    },
  });

  const del = useMutation({
    mutationFn: async () => (await api.delete(`/events/${id}`)).data,
    onSuccess: () => {
      toast.success("Event deleted");
      qc.invalidateQueries({ queryKey: ["events"] });
      nav({ to: "/events" });
    },
  });

  const changeStatus = useMutation({
    mutationFn: async (status: string) =>
      (await api.patch(`/events/${id}`, { status })).data,
    onSuccess: (data) => {
      toast.success(`Status set to ${data.status}`);
      qc.invalidateQueries({ queryKey: ["event", id] });
      qc.invalidateQueries({ queryKey: ["events"] });
    },
    onError: () => toast.error("Failed to update status"),
  });

  const e = event.data;
  const p = prediction.data;
  const r = resources.data;
  const rts: RouteSuggestion[] = Array.isArray(routes.data) ? routes.data : [];
  const hm = heatmap.data;

  return (
    <div className="p-6 lg:p-8 space-y-6">
      <PageHeader
        title={e?.name ?? "Event"}
        subtitle={
          e
            ? `${e.event_type} • ${e.location_name} • ${formatIST(e.start_datetime, "MMM d, yyyy HH:mm")} → ${formatIST(e.end_datetime, "HH:mm")} • ${e.status?.toUpperCase() ?? ""}`
            : "Loading…"
        }
        actions={
          <>
            <Button
              variant="outline"
              onClick={() =>
                openCopilot({ eventId: Number(id), eventLabel: e?.name })
              }
            >
              <Bot className="h-4 w-4 mr-1" /> Ask EATIS AI
            </Button>
            {can(["operator", "admin"]) && (
              <>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="secondary">
                      Status: {e?.status ?? "…"}
                      <ChevronDown className="h-3 w-3 ml-1" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuLabel className="text-xs mono uppercase text-muted-foreground">
                      Change Status
                    </DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    {(["scheduled", "active", "completed", "cancelled"] as const).map((s) => (
                      <DropdownMenuItem
                        key={s}
                        onClick={() => changeStatus.mutate(s)}
                        disabled={e?.status === s || changeStatus.isPending}
                        className="capitalize"
                      >
                        {s}
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuContent>
                </DropdownMenu>
                <Button variant="secondary" asChild>
                  <Link to="/events/$id/edit" params={{ id }}>
                    <Pencil className="h-4 w-4 mr-1" /> Edit
                  </Link>
                </Button>
              </>
            )}
            {can(["admin"]) && (
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="destructive">
                    <Trash2 className="h-4 w-4 mr-1" /> Delete
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Delete event?</AlertDialogTitle>
                    <AlertDialogDescription>
                      This cannot be undone.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction onClick={() => del.mutate()}>
                      Delete
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            )}
          </>
        }
      />

      <div className="grid lg:grid-cols-2 gap-6">
        <Panel
          title="Prediction"
          actions={
            can(["operator", "admin"]) && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => rerunPred.mutate()}
                disabled={rerunPred.isPending}
              >
                <RefreshCw className="h-3 w-3 mr-1" /> Re-run
              </Button>
            )
          }
        >
          {prediction.isLoading && <div className="text-muted-foreground">Loading…</div>}
          {prediction.isError && (
            <div className="text-sm text-muted-foreground">No prediction yet.</div>
          )}
          {p && (
            <div className="space-y-4">
              <SeverityChip level={p.congestion_level} className="text-base px-3 py-1" />
              <div className="grid grid-cols-2 gap-4">
                <Metric label="Risk Score" value={p.risk_score?.toFixed?.(1) ?? "—"} />
                {/* backend field: delay_time_minutes */}
                <Metric label="Delay" value={`${p.delay_time_minutes ?? "—"} min`} />
                <Metric
                  label="Impact Radius"
                  value={`${p.impact_radius_km?.toFixed?.(1) ?? "—"} km`}
                />
                <Metric
                  label="Confidence"
                  value={`${((p.confidence_score ?? 0) * 100).toFixed(0)}%`}
                />
              </div>
            </div>
          )}
        </Panel>

        <Panel
          title="Resource Allocation"
          actions={
            can(["operator", "admin"]) && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => recompResources.mutate()}
                disabled={recompResources.isPending}
              >
                <RefreshCw className="h-3 w-3 mr-1" /> Recompute
              </Button>
            )
          }
        >
          {resources.isError && (
            <div className="text-sm text-muted-foreground">No allocation yet.</div>
          )}
          {r && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                {/* backend fields: officers_required, barricades_required */}
                <ResStat icon={Users} label="Officers" value={r.officers_required} />
                <ResStat icon={Construction} label="Barricades" value={r.barricades_required} />
                <ResStat icon={Car} label="Patrols" value={r.patrol_vehicles} />
                <ResStat icon={Ambulance} label="Emergency" value={r.emergency_units} />
                <ResStat icon={Truck} label="Tow" value={r.tow_vehicles} />
              </div>
              {r.deployment_notes && (
                <p className="text-sm text-muted-foreground border-t border-border pt-3 whitespace-pre-wrap">
                  {r.deployment_notes}
                </p>
              )}
            </div>
          )}
        </Panel>
      </div>

      <Panel title="Congestion Heatmap">
        {hm && e && (
          <>
            <MapView
              center={[e.latitude, e.longitude]}
              zoom={14}
              heatPoints={hm.points}
              markers={[
                {
                  lat: e.latitude,
                  lng: e.longitude,
                  color: severityHex[p?.congestion_level ?? "medium"],
                  label: e.name,
                },
              ]}
              height="420px"
            />
            <div className="mt-3 flex flex-wrap gap-2">
              {(hm.zones ?? []).map((z, i) => (
                <div key={z.name ?? i} className="flex items-center gap-2 text-xs">
                  <SeverityChip level={z.level ?? "low"} />
                  <span className="mono">{z.name ?? z.location_name}</span>
                </div>
              ))}
            </div>
          </>
        )}
        {heatmap.isError && (
          <div className="text-sm text-muted-foreground">No heatmap data yet.</div>
        )}
      </Panel>

      <Panel
        title="Diversion Routes"
        actions={
          can(["operator", "admin"]) && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => regenRoutes.mutate()}
              disabled={regenRoutes.isPending}
            >
              <RefreshCw className="h-3 w-3 mr-1" /> Regenerate
            </Button>
          )
        }
      >
        {routes.isError && (
          <div className="text-sm text-muted-foreground">No routes generated yet.</div>
        )}
        {e && rts.length > 0 && (
          <div className="grid lg:grid-cols-3 gap-4">
            <div className="lg:col-span-2">
              <MapView
                center={[e.latitude, e.longitude]}
                zoom={13}
                height="380px"
                markers={[{ lat: e.latitude, lng: e.longitude, color: "#F2A900" }]}
                polylines={rts
                  .map((rt) => ({
                    coords: parseCoords(rt.geojson_coordinates),
                    color: "#2D6CDF",
                    label: rt.route_name,
                  }))
                  .filter((rt) => rt.coords.length >= 2)}
              />
            </div>
            <ul className="space-y-3">
              {rts.map((rt) => (
                <li
                  key={rt.id ?? rt.route_name}
                  className="border border-border rounded-md p-3 bg-accent/30"
                >
                  <div className="flex items-center justify-between">
                    {/* backend field: route_name */}
                    <span className="font-medium">{rt.route_name}</span>
                    <span className="mono text-[10px] uppercase text-muted-foreground">
                      {rt.route_type}
                    </span>
                  </div>
                  {rt.description && (
                    <p className="text-xs text-muted-foreground mt-1">{rt.description}</p>
                  )}
                  <div className="flex gap-3 mt-2 mono text-xs">
                    <span>{rt.distance_km?.toFixed?.(1) ?? "—"} km</span>
                    <span>{rt.estimated_time_minutes ?? "—"} min</span>
                  </div>
                  {/* backend field: diversion_benefit */}
                  {rt.diversion_benefit && (
                    <p className="text-xs text-route-blue mt-1">{rt.diversion_benefit}</p>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}
      </Panel>

      {e?.status === "completed" && (
        <Panel title="Post-Event Analysis">
          {postEvent.isLoading && <div className="text-muted-foreground">Loading…</div>}
          {postEvent.data ? (
            <PostEventReport data={postEvent.data} />
          ) : (
            can(["operator", "admin"]) && <PostEventForm eventId={Number(id)} />
          )}
        </Panel>
      )}
    </div>
  );
}

function ResStat({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: number;
}) {
  return (
    <div className="bg-accent/40 p-3 rounded-md text-center">
      <Icon className="h-4 w-4 mx-auto text-muted-foreground" />
      <div className="display text-xl mt-1">{value}</div>
      <div className="text-[10px] mono uppercase text-muted-foreground">{label}</div>
    </div>
  );
}
