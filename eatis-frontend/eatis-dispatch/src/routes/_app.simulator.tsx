import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/AppShell";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { SeverityChip } from "@/components/SeverityChip";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  FlaskConical,
  ArrowRight,
  Users,
  ShieldAlert,
  Clock,
  RadioTower,
  TrendingUp,
  Car,
  Truck,
  Siren,
  TrafficCone,
} from "lucide-react";
import type { Prediction, ResourceAllocation } from "@/lib/types";
import { toast } from "sonner";

export const Route = createFileRoute("/_app/simulator")({
  component: Simulator,
});

const EVENT_TYPES = [
  { value: "political_rally", label: "Political Rally" },
  { value: "sports_event", label: "Sports Event" },
  { value: "music_festival", label: "Music Festival" },
  { value: "cultural_event", label: "Cultural Event" },
  { value: "religious_gathering", label: "Religious Gathering" },
  { value: "construction", label: "Construction" },
  { value: "public_demonstration", label: "Public Demonstration" },
  { value: "marathon", label: "Marathon" },
  { value: "parade", label: "Parade" },
  { value: "exhibition", label: "Exhibition" },
  { value: "other", label: "Other" },
];

interface SimResponse {
  prediction: Prediction;
  recommended_resources: ResourceAllocation;
}

type SimForm = {
  // Core identity
  name: string;
  description: string;
  event_type: string;
  // Location
  location_name: string;
  address: string;
  latitude: string;
  longitude: string;
  // Timing
  start_datetime: string;
  end_datetime: string;
  // Characteristics
  expected_crowd_size: string;
  road_closure: boolean;
  road_closure_details: string;
};

const defaultForm: SimForm = {
  name: "",
  description: "",
  event_type: "",
  location_name: "",
  address: "",
  latitude: "",
  longitude: "",
  start_datetime: "",
  end_datetime: "",
  expected_crowd_size: "",
  road_closure: false,
  road_closure_details: "",
};

function Simulator() {
  const nav = useNavigate();
  const [form, setForm] = useState<SimForm>(defaultForm);
  const f = (patch: Partial<SimForm>) => setForm((p) => ({ ...p, ...patch }));

  // Compute duration in hours from start/end for the API payload
  const durationHours = (() => {
    if (!form.start_datetime || !form.end_datetime) return 4;
    const diff =
      (new Date(form.end_datetime).getTime() - new Date(form.start_datetime).getTime()) /
      3600000;
    return diff > 0 ? diff : 4;
  })();

  const sim = useMutation({
    mutationFn: async () => {
      if (!form.start_datetime) {
        throw new Error("Start date/time is required to run simulation");
      }
      const payload = {
        event_type: form.event_type,
        latitude: parseFloat(form.latitude) || 0,
        longitude: parseFloat(form.longitude) || 0,
        start_datetime: new Date(form.start_datetime).toISOString(),
        expected_crowd_size: parseInt(form.expected_crowd_size, 10) || 1000,
        duration_hours: durationHours,
        has_road_closure: form.road_closure,
      };
      return (await api.post<SimResponse>("/events/simulate", payload)).data;
    },
    onError: (err) => {
      const msg = err instanceof Error ? err.message : "Simulation failed";
      toast.error(msg);
    },
  });

  const result = sim.data;

  const convert = () => {
    const params = new URLSearchParams({
      name: form.name,
      description: form.description,
      event_type: form.event_type,
      location_name: form.location_name,
      address: form.address,
      latitude: form.latitude,
      longitude: form.longitude,
      start_datetime: form.start_datetime,
      end_datetime: form.end_datetime,
      expected_crowd_size: form.expected_crowd_size,
      road_closure: String(form.road_closure),
      road_closure_details: form.road_closure_details,
    });
    nav({ to: `/events/new?${params.toString()}` as never });
  };

  return (
    <div className="p-6 lg:p-8 space-y-6">
      <PageHeader
        title="Event Simulator"
        subtitle="What-if analysis — nothing is persisted until you convert"
        actions={
          result ? (
            <Button onClick={convert} className="gap-2">
              Convert to Real Event <ArrowRight className="h-4 w-4" />
            </Button>
          ) : undefined
        }
      />

      <div className="grid lg:grid-cols-2 gap-6 items-start">
        {/* ── Left: Full event form ── */}
        <Card className="p-5 space-y-5">
          <div className="flex items-center gap-2 mb-1">
            <FlaskConical className="h-4 w-4 text-primary" />
            <span className="display text-sm uppercase tracking-widest text-muted-foreground">
              Event Details
            </span>
          </div>

          {/* Identity */}
          <section className="space-y-3">
            <div className="text-[10px] uppercase mono text-muted-foreground tracking-widest border-b border-border pb-1">
              Identity
            </div>
            <div className="space-y-2">
              <Label>Event Name</Label>
              <Input
                placeholder="e.g. Bangalore Music Fest 2026"
                value={form.name}
                onChange={(e) => f({ name: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>Event Type</Label>
              <Select value={form.event_type || undefined} onValueChange={(v) => f({ event_type: v })}>
                <SelectTrigger>
                  <SelectValue placeholder="Select event type..." />
                </SelectTrigger>
                <SelectContent>
                  {EVENT_TYPES.map((t) => (
                    <SelectItem key={t.value} value={t.value}>
                      {t.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Description</Label>
              <Textarea
                placeholder="Brief description of the event…"
                value={form.description}
                onChange={(e) => f({ description: e.target.value })}
                rows={2}
              />
            </div>
          </section>

          {/* Location */}
          <section className="space-y-3">
            <div className="text-[10px] uppercase mono text-muted-foreground tracking-widest border-b border-border pb-1">
              Location
            </div>
            <div className="space-y-2">
              <Label>Location Name</Label>
              <Input
                placeholder="e.g. Palace Grounds, Bengaluru"
                value={form.location_name}
                onChange={(e) => f({ location_name: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>Address</Label>
              <Input
                placeholder="Full address"
                value={form.address}
                onChange={(e) => f({ address: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>Latitude</Label>
                <Input
                  type="number"
                  step="any"
                  placeholder="12.9716"
                  value={form.latitude}
                  onChange={(e) => f({ latitude: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>Longitude</Label>
                <Input
                  type="number"
                  step="any"
                  placeholder="77.5946"
                  value={form.longitude}
                  onChange={(e) => f({ longitude: e.target.value })}
                />
              </div>
            </div>
          </section>

          {/* Timing */}
          <section className="space-y-3">
            <div className="text-[10px] uppercase mono text-muted-foreground tracking-widest border-b border-border pb-1">
              Timing
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label>Start Date/Time</Label>
                <Input
                  type="datetime-local"
                  value={form.start_datetime}
                  onChange={(e) => f({ start_datetime: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label>End Date/Time</Label>
                <Input
                  type="datetime-local"
                  value={form.end_datetime}
                  onChange={(e) => f({ end_datetime: e.target.value })}
                />
              </div>
            </div>
            {form.start_datetime && form.end_datetime && durationHours > 0 && (
              <p className="text-xs text-muted-foreground mono">
                Duration: {durationHours.toFixed(1)} hours
              </p>
            )}
          </section>

          {/* Characteristics */}
          <section className="space-y-3">
            <div className="text-[10px] uppercase mono text-muted-foreground tracking-widest border-b border-border pb-1">
              Characteristics
            </div>
            <div className="space-y-2">
              <Label>Expected Crowd Size</Label>
              <Input
                type="number"
                min="1"
                placeholder="5000"
                value={form.expected_crowd_size}
                onChange={(e) => f({ expected_crowd_size: e.target.value })}
              />
            </div>
            <div className="flex items-center gap-3">
              <Switch
                id="closure"
                checked={form.road_closure}
                onCheckedChange={(v) => f({ road_closure: v })}
              />
              <Label htmlFor="closure">Road closure required</Label>
            </div>
            {form.road_closure && (
              <div className="space-y-2">
                <Label>Closure Details</Label>
                <Textarea
                  placeholder="Which roads/areas will be closed?"
                  value={form.road_closure_details}
                  onChange={(e) => f({ road_closure_details: e.target.value })}
                  rows={2}
                />
              </div>
            )}
          </section>

          <Button
            className="w-full gap-2"
            onClick={() => sim.mutate()}
            disabled={sim.isPending}
          >
            <FlaskConical className="h-4 w-4" />
            {sim.isPending ? "Running Simulation…" : "Run Simulation"}
          </Button>
        </Card>

        {/* ── Right: Results ── */}
        <div className="space-y-4 sticky top-[72px] lg:top-6">
          {!result && !sim.isPending && (
            <Card className="p-8 flex flex-col items-center justify-center gap-4 text-center min-h-64">
              <div className="h-14 w-14 rounded-2xl bg-primary/10 flex items-center justify-center">
                <FlaskConical className="h-7 w-7 text-primary" />
              </div>
              <div>
                <p className="font-semibold">No simulation yet</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Fill in event details and click Run Simulation to see predictions
                </p>
              </div>
            </Card>
          )}

          {sim.isPending && (
            <Card className="p-8 flex flex-col items-center justify-center gap-3 min-h-64">
              <div className="h-10 w-10 rounded-full border-2 border-primary border-t-transparent animate-spin" />
              <p className="text-sm text-muted-foreground">Running simulation…</p>
            </Card>
          )}

          {result && (
            <>
              {/* Congestion + Key Metrics */}
              <Card className="p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <span className="display text-xs uppercase tracking-widest text-muted-foreground">
                    Predicted Congestion
                  </span>
                  <SeverityChip level={result.prediction.congestion_level} className="text-sm px-3 py-1" />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <Metric
                    icon={ShieldAlert}
                    label="Risk Score"
                    value={`${result.prediction.risk_score?.toFixed?.(1) ?? "—"} / 100`}
                  />
                  <Metric
                    icon={Clock}
                    label="Est. Delay"
                    value={`${result.prediction.delay_time_minutes ?? "—"} min`}
                  />
                  <Metric
                    icon={RadioTower}
                    label="Impact Radius"
                    value={`${result.prediction.impact_radius_km?.toFixed?.(1) ?? "—"} km`}
                  />
                  <Metric
                    icon={TrendingUp}
                    label="Confidence"
                    value={`${((result.prediction.confidence_score ?? 0) * 100).toFixed(0)}%`}
                  />
                </div>
              </Card>

              {/* Resources */}
              <Card className="p-5">
                <div className="display text-xs uppercase tracking-widest text-muted-foreground mb-3">
                  Recommended Resources
                </div>
                <div className="space-y-2">
                  <ResRow icon={Users} label="Officers Required" value={result.recommended_resources.officers_required} />
                  <ResRow icon={TrafficCone} label="Barricades" value={result.recommended_resources.barricades_required} />
                  <ResRow icon={Car} label="Patrol Vehicles" value={result.recommended_resources.patrol_vehicles} />
                  <ResRow icon={Siren} label="Emergency Units" value={result.recommended_resources.emergency_units} />
                  <ResRow icon={Truck} label="Tow Vehicles" value={result.recommended_resources.tow_vehicles} />
                </div>
              </Card>

              {/* Convert CTA */}
              <Card className="p-4 border-primary/40 bg-primary/5">
                <div className="flex items-start gap-3">
                  <div className="flex-1">
                    <p className="font-medium text-sm">Ready to create this event?</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      All your simulation data will be pre-filled in the event creation form.
                    </p>
                  </div>
                  <Button onClick={convert} size="sm" className="gap-1 shrink-0">
                    Convert <ArrowRight className="h-3 w-3" />
                  </Button>
                </div>
              </Card>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function Metric({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="bg-accent/40 rounded-md p-3 flex items-center gap-3">
      <Icon className="h-4 w-4 text-muted-foreground shrink-0" />
      <div>
        <div className="text-[10px] uppercase mono text-muted-foreground tracking-widest">{label}</div>
        <div className="mono text-base font-semibold mt-0.5">{value}</div>
      </div>
    </div>
  );
}

function ResRow({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: number;
}) {
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-border/50 last:border-0">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Icon className="h-3.5 w-3.5" />
        {label}
      </div>
      <Badge variant="secondary" className="mono font-semibold">
        {value}
      </Badge>
    </div>
  );
}
