import { createFileRoute, redirect } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { api, getToken } from "@/lib/api";
import { PageHeader } from "@/components/AppShell";
import { Card } from "@/components/ui/card";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import type { AnalyticsDashboard } from "@/lib/types";
import { SeverityChip, severityHex } from "@/components/SeverityChip";

export const Route = createFileRoute("/_app/analytics")({
  beforeLoad: () => {
    if (typeof window !== "undefined" && !getToken()) {
      throw redirect({ to: "/login" });
    }
  },
  component: AnalyticsPage,
});

function AnalyticsPage() {
  const q = useQuery({
    queryKey: ["analytics", "dashboard"],
    queryFn: async () => (await api.get<AnalyticsDashboard>("/analytics/dashboard")).data,
    retry: false,
  });
  const a = q.data;
  const s = a?.summary;

  // Convert events_by_type dict to chart array: { type, count }[]
  const eventsByType = Object.entries(s?.events_by_type ?? {}).map(([type, count]) => ({
    type,
    count,
  }));

  // Convert congestion_distribution dict to chart array: { level, count }[]
  const congestionDist = Object.entries(s?.congestion_distribution ?? {}).map(([level, count]) => ({
    level,
    count,
  }));

  // Trends for line chart
  const trends = (a?.trends ?? []).map((t) => ({
    month: t.period,
    event_count: t.event_count,
    avg_risk_score: t.avg_risk_score,
  }));

  return (
    <div className="p-6 lg:p-8 space-y-6">
      <PageHeader title="Analytics" subtitle="System-wide event traffic insights" />
      {q.isLoading && <div className="text-muted-foreground">Loading…</div>}
      {q.isError && (
        <Card className="p-8 text-center text-muted-foreground">
          Analytics requires Analyst role or above.
        </Card>
      )}
      {s && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <StatCard label="Total" value={s.total_events} />
            <StatCard label="Active" value={s.active_events} />
            <StatCard label="Scheduled" value={s.scheduled_events} />
            <StatCard label="Completed" value={s.completed_events} />
            <StatCard label="Cancelled" value={s.cancelled_events} />
          </div>

          <div className="grid lg:grid-cols-2 gap-6">
            <Card className="p-5">
              <ChartTitle>Events by Type</ChartTitle>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={eventsByType}>
                  <CartesianGrid stroke="#3a3d44" strokeDasharray="3 3" />
                  <XAxis dataKey="type" stroke="#9ca0a8" fontSize={11} />
                  <YAxis stroke="#9ca0a8" fontSize={11} />
                  <Tooltip
                    contentStyle={{ background: "#2A2D33", border: "1px solid #3a3d44" }}
                  />
                  <Bar dataKey="count" fill="#F2A900" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Card>

            <Card className="p-5">
              <ChartTitle>Congestion Distribution</ChartTitle>
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie
                    data={congestionDist}
                    dataKey="count"
                    nameKey="level"
                    outerRadius={90}
                    label
                  >
                    {congestionDist.map((d) => (
                      <Cell
                        key={d.level}
                        fill={severityHex[d.level as keyof typeof severityHex] ?? "#888"}
                      />
                    ))}
                  </Pie>
                  <Legend />
                  <Tooltip
                    contentStyle={{ background: "#2A2D33", border: "1px solid #3a3d44" }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </Card>
          </div>

          <Card className="p-5">
            <ChartTitle>Trend Over Time</ChartTitle>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trends}>
                <CartesianGrid stroke="#3a3d44" strokeDasharray="3 3" />
                <XAxis dataKey="month" stroke="#9ca0a8" fontSize={11} />
                <YAxis yAxisId="left" stroke="#9ca0a8" fontSize={11} />
                <YAxis yAxisId="right" orientation="right" stroke="#9ca0a8" fontSize={11} />
                <Tooltip
                  contentStyle={{ background: "#2A2D33", border: "1px solid #3a3d44" }}
                />
                <Legend />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="event_count"
                  stroke="#F2A900"
                  name="Events"
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="avg_risk_score"
                  stroke="#2D6CDF"
                  name="Avg Risk"
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>

          <div className="grid lg:grid-cols-2 gap-6">
            <Card className="p-5">
              <ChartTitle>Resource Usage Totals</ChartTitle>
              <div className="grid grid-cols-2 gap-3 mt-2">
                {Object.entries(s.total_resources_allocated ?? {}).map(([k, v]) => (
                  <div key={k} className="bg-accent/40 p-3 rounded-md">
                    <div className="text-[10px] mono uppercase text-muted-foreground">
                      {k.replace(/_/g, " ")}
                    </div>
                    <div className="display text-2xl">{v}</div>
                  </div>
                ))}
              </div>
            </Card>

            <Card className="p-5">
              <ChartTitle>High-Risk Zones</ChartTitle>
              <table className="w-full text-sm">
                <thead className="text-xs uppercase mono text-muted-foreground text-left">
                  <tr>
                    <th className="py-2">Zone</th>
                    <th>Events</th>
                    <th>Score</th>
                  </tr>
                </thead>
                <tbody>
                  {(a?.high_risk_zones ?? []).map((z) => (
                    <tr key={z.location_name} className="border-t border-border">
                      <td className="py-2">{z.location_name}</td>
                      <td className="mono">{z.event_count}</td>
                      <td>
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
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <Card className="p-4">
      <div className="text-[10px] uppercase mono tracking-widest text-muted-foreground">
        {label}
      </div>
      <div className="display text-3xl mt-1">{value}</div>
    </Card>
  );
}

function ChartTitle({ children }: { children: React.ReactNode }) {
  return (
    <div className="display uppercase text-xs tracking-widest text-muted-foreground mb-3">
      {children}
    </div>
  );
}
