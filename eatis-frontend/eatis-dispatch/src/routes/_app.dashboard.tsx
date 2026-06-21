import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { formatIST } from "@/lib/utils";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/AppShell";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { SeverityChip } from "@/components/SeverityChip";
import type { AnalyticsDashboard, PaginatedEvents, EventItem } from "@/lib/types";
import { Plus, FlaskConical, Bot, AlertTriangle, Activity, TrendingUp, Calendar } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { openCopilot } from "@/components/CopilotLauncher";

export const Route = createFileRoute("/_app/dashboard")({
  component: Dashboard,
});

function Stat({
  label,
  value,
  icon: Icon,
  accent,
}: {
  label: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  accent?: string;
}) {
  return (
    <Card className="p-4 flex items-center gap-4">
      <div
        className={`h-11 w-11 rounded-md flex items-center justify-center ${accent ?? "bg-accent"}`}
      >
        <Icon className="h-5 w-5" />
      </div>
      <div>
        <div className="text-[11px] uppercase mono tracking-widest text-muted-foreground">
          {label}
        </div>
        <div className="display text-2xl">{value}</div>
      </div>
    </Card>
  );
}

function Dashboard() {
  const { can } = useAuth();

  // Analytics — requires analyst+ role; fails gracefully for viewer
  const analytics = useQuery({
    queryKey: ["analytics", "dashboard"],
    queryFn: async () => (await api.get<AnalyticsDashboard>("/analytics/dashboard")).data,
    retry: false,
  });

  // Events list — backend returns { total, skip, limit, data: [...] }
  const active = useQuery({
    queryKey: ["events", { status: "active" }],
    queryFn: async () =>
      (await api.get<PaginatedEvents>("/events", { params: { status: "active", limit: 50 } })).data,
  });

  const scheduled = useQuery({
    queryKey: ["events", { status: "scheduled" }],
    queryFn: async () =>
      (await api.get<PaginatedEvents>("/events", { params: { status: "scheduled", limit: 50 } })).data,
  });

  const toArr = (d: PaginatedEvents | undefined): EventItem[] => d?.data ?? [];

  const s = analytics.data?.summary;
  const events = [...toArr(active.data), ...toArr(scheduled.data)].slice(0, 10);

  return (
    <div className="p-6 lg:p-8">
      <PageHeader
        title="Dispatch Dashboard"
        subtitle="Live event traffic intelligence"
        actions={
          <>
            {can(["operator", "admin"]) && (
              <Button asChild>
                <Link to="/events/new">
                  <Plus className="h-4 w-4 mr-1" /> New Event
                </Link>
              </Button>
            )}
            <Button variant="secondary" asChild>
              <Link to="/simulator">
                <FlaskConical className="h-4 w-4 mr-1" /> Simulate
              </Link>
            </Button>
            <Button variant="outline" onClick={() => openCopilot()}>
              <Bot className="h-4 w-4 mr-1" /> Copilot
            </Button>
          </>
        }
      />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <Stat label="Total Events" value={s?.total_events ?? "—"} icon={Calendar} />
        <Stat
          label="Active"
          value={s?.active_events ?? "—"}
          icon={Activity}
          accent="bg-primary/20"
        />
        <Stat
          label="High Risk"
          value={s?.high_risk_events ?? "—"}
          icon={AlertTriangle}
          accent="bg-sev-critical/25"
        />
        <Stat
          label="Avg Risk Score"
          value={s?.avg_risk_score?.toFixed?.(1) ?? "—"}
          icon={TrendingUp}
        />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2 p-5">
          <div className="display uppercase text-sm tracking-wider mb-4 text-muted-foreground">
            Active &amp; Upcoming Events
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-xs uppercase text-muted-foreground mono">
                <tr>
                  <th className="py-2">Name</th>
                  <th>Type</th>
                  <th>Location</th>
                  <th>Start</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {events.length === 0 && (
                  <tr>
                    <td colSpan={5} className="text-muted-foreground py-6 text-center">
                      {active.isLoading || scheduled.isLoading ? "Loading…" : "No events"}
                    </td>
                  </tr>
                )}
                {events.map((e) => (
                  <tr
                    key={e.id}
                    className="border-t border-border hover:bg-accent/40 transition-colors"
                  >
                    <td className="py-2">
                      <Link
                        to="/events/$id"
                        params={{ id: String(e.id) }}
                        className="text-primary hover:underline"
                      >
                        {e.name}
                      </Link>
                    </td>
                    <td className="mono text-xs">{e.event_type}</td>
                    <td>{e.location_name}</td>
                    <td className="mono text-xs">
                      {e.start_datetime ? formatIST(e.start_datetime, "MMM d, HH:mm") : "—"}
                    </td>
                    <td>
                      <span className="mono text-xs uppercase">{e.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        <Card className="p-5">
          <div className="display uppercase text-sm tracking-wider mb-4 text-muted-foreground">
            High-Risk Zones
          </div>
          <ul className="space-y-3">
            {(analytics.data?.high_risk_zones ?? []).slice(0, 6).map((z) => (
              <li key={z.location_name} className="flex items-center justify-between text-sm">
                <span>{z.location_name}</span>
                <SeverityChip
                  level={
                    z.avg_risk_score >= 80
                      ? "critical"
                      : z.avg_risk_score >= 60
                        ? "high"
                        : z.avg_risk_score >= 40
                          ? "medium"
                          : "low"
                  }
                />
              </li>
            ))}
            {(analytics.data?.high_risk_zones ?? []).length === 0 && !analytics.isLoading && (
              <li className="text-muted-foreground text-sm">No high-risk zones</li>
            )}
          </ul>
        </Card>
      </div>
    </div>
  );
}
