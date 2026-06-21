import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/AppShell";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { EventItem, PostEventAnalysis, PaginatedEvents } from "@/lib/types";
import { PostEventForm, PostEventReport } from "@/components/PostEventViews";
import { formatIST } from "@/lib/utils";
import { useAuth } from "@/lib/auth";

export const Route = createFileRoute("/_app/post-event")({
  component: PostEventPage,
});

function PostEventPage() {
  const { can } = useAuth();
  const [selected, setSelected] = useState<EventItem | null>(null);

  const events = useQuery({
    queryKey: ["events", { status: "completed" }],
    queryFn: async () =>
      (
        await api.get<PaginatedEvents>("/events", {
          params: { status: "completed", limit: 100 },
        })
      ).data,
  });

  // Backend returns { total, skip, limit, data: [...] }
  const list: EventItem[] = events.data?.data ?? [];

  const analysis = useQuery({
    queryKey: ["post-event", String(selected?.id)],
    queryFn: async () =>
      (await api.get<PostEventAnalysis>(`/post-event/${selected!.id}`)).data,
    enabled: !!selected,
    retry: false,
  });

  return (
    <div className="p-6 lg:p-8">
      <PageHeader title="Post-Event Analysis" subtitle="Predicted vs. actual outcomes" />
      <div className="grid lg:grid-cols-[340px_1fr] gap-6">
        <Card className="p-3 max-h-[calc(100vh-200px)] overflow-y-auto">
          <div className="display uppercase text-xs tracking-widest text-muted-foreground p-2">
            Completed Events
          </div>
          <ul className="space-y-1">
            {list.map((e) => (
              <li key={e.id}>
                <button
                  onClick={() => setSelected(e)}
                  className={`w-full text-left p-2 rounded-md text-sm transition-colors ${
                    selected?.id === e.id ? "bg-primary/20 border-l-2 border-primary" : "hover:bg-accent"
                  }`}
                >
                  <div className="font-medium truncate">{e.name}</div>
                  <div className="text-[11px] mono text-muted-foreground">
                  {formatIST(e.start_datetime, "MMM d, yyyy")}
                  </div>
                </button>
              </li>
            ))}
            {list.length === 0 && !events.isLoading && (
              <li className="text-sm text-muted-foreground p-3">No completed events.</li>
            )}
          </ul>
        </Card>

        <div>
          {!selected && (
            <Card className="p-8 text-center text-muted-foreground">
              Select a completed event to view or submit analysis.
            </Card>
          )}
          {selected && (
            <Card className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h2 className="display text-2xl">{selected.name}</h2>
                  <p className="text-sm text-muted-foreground mono">
                    {selected.location_name}
                  </p>
                </div>
                <Button asChild variant="outline" size="sm">
                  <a href={`/events/${selected.id}`}>Open Command Center</a>
                </Button>
              </div>
              {analysis.isLoading && (
                <div className="text-muted-foreground">Loading…</div>
              )}
              {analysis.data ? (
                <PostEventReport data={analysis.data} />
              ) : (
                can(["operator", "admin"]) ? (
                  <PostEventForm eventId={selected.id} />
                ) : (
                  <p className="text-sm text-muted-foreground">
                    No analysis submitted yet.
                  </p>
                )
              )}
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
