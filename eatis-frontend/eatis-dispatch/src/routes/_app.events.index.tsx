import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { formatIST } from "@/lib/utils";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/AppShell";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { EventItem, EventStatus, PaginatedEvents } from "@/lib/types";
import { Plus } from "lucide-react";
import { useAuth } from "@/lib/auth";

export const Route = createFileRoute("/_app/events/")(
  {
    component: EventsList,
  }
);

const EVENT_TYPES: { value: string; label: string }[] = [
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

function EventsList() {
  const { can } = useAuth();
  const nav = useNavigate();
  const [status, setStatus] = useState<EventStatus | "all">("all");
  const [eventType, setEventType] = useState<string>("all");
  const [skip, setSkip] = useState(0);
  const limit = 20;
  const [search, setSearch] = useState("");

  const params: Record<string, string | number> = { skip, limit };
  if (status !== "all") params.status = status;
  if (eventType !== "all") params.event_type = eventType;

  const q = useQuery({
    queryKey: ["events", params],
    queryFn: async () => (await api.get<PaginatedEvents>("/events", { params })).data,
  });

  // Backend returns { total, skip, limit, data: [...] }
  const items: EventItem[] = q.data?.data ?? [];
  const total: number = q.data?.total ?? 0;

  const filtered = items.filter((e) =>
    search ? e.name.toLowerCase().includes(search.toLowerCase()) : true,
  );

  return (
    <div className="p-6 lg:p-8">
      <PageHeader
        title="Events"
        subtitle={`${total} total`}
        actions={
          can(["operator", "admin"]) && (
            <Button asChild>
              <Link to="/events/new">
                <Plus className="h-4 w-4 mr-1" /> New Event
              </Link>
            </Button>
          )
        }
      />

      <Card className="p-4 mb-4 flex flex-wrap gap-3 items-end">
        <div className="flex-1 min-w-[180px]">
          <label className="text-xs mono uppercase text-muted-foreground">Search</label>
          <Input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Name…" />
        </div>
        <div>
          <label className="text-xs mono uppercase text-muted-foreground block mb-1">Status</label>
          <Select value={status} onValueChange={(v) => setStatus(v as EventStatus | "all")}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="scheduled">Scheduled</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
              <SelectItem value="cancelled">Cancelled</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div>
          <label className="text-xs mono uppercase text-muted-foreground block mb-1">Type</label>
          <Select value={eventType} onValueChange={setEventType}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              {EVENT_TYPES.map((t) => (
                <SelectItem key={t.value} value={t.value}>
                  {t.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </Card>

      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-accent/40 text-left text-xs uppercase mono text-muted-foreground">
              <tr>
                <th className="px-4 py-3 whitespace-nowrap">Name</th>
                <th className="pr-4 whitespace-nowrap">Type</th>
                <th className="pr-4 whitespace-nowrap">Location</th>
                <th className="pr-4 whitespace-nowrap">Start</th>
                <th className="pr-4 whitespace-nowrap">Crowd</th>
                <th className="pr-4 whitespace-nowrap">Status</th>
              </tr>
            </thead>
          <tbody>
            {q.isLoading && (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-muted-foreground">
                  Loading…
                </td>
              </tr>
            )}
            {!q.isLoading && filtered.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-muted-foreground">
                  No events found
                </td>
              </tr>
            )}
            {filtered.map((e) => (
              <tr
                key={e.id}
                onClick={() => nav({ to: "/events/$id", params: { id: String(e.id) } })}
                className="border-t border-border cursor-pointer hover:bg-accent/30"
              >
                <td className="px-4 py-3 font-medium whitespace-nowrap">{e.name}</td>
                <td className="pr-4 mono text-xs whitespace-nowrap text-muted-foreground">{e.event_type}</td>
                <td className="pr-4 whitespace-nowrap truncate max-w-[200px]" title={e.location_name}>{e.location_name}</td>
                <td className="pr-4 mono text-xs whitespace-nowrap">
                  {e.start_datetime ? formatIST(e.start_datetime, "MMM d, yyyy HH:mm") : "—"}
                </td>
                <td className="pr-4 mono text-xs whitespace-nowrap">{e.expected_crowd_size?.toLocaleString()}</td>
                <td className="pr-4 whitespace-nowrap">
                  <span className="mono text-[10px] uppercase bg-accent px-2 py-1 rounded-md">{e.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
      </Card>

      <div className="flex justify-between items-center mt-4 text-sm">
        <span className="mono text-xs text-muted-foreground">
          {skip + 1}–{Math.min(skip + limit, total)} of {total}
        </span>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={skip === 0}
            onClick={() => setSkip(Math.max(0, skip - limit))}
          >
            Prev
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={skip + limit >= total}
            onClick={() => setSkip(skip + limit)}
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  );
}
