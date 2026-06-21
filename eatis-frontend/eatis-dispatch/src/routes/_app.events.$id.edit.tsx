import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/AppShell";
import { EventForm } from "@/components/EventForm";
import type { EventItem } from "@/lib/types";

export const Route = createFileRoute("/_app/events/$id/edit")({
  component: EditEventPage,
});

function EditEventPage() {
  const { id } = Route.useParams();
  const q = useQuery({
    queryKey: ["event", id],
    queryFn: async () => (await api.get<EventItem>(`/events/${id}`)).data,
  });

  return (
    <div className="p-6 lg:p-8 max-w-4xl">
      <PageHeader title="Edit Event" />
      {q.isLoading && <div className="text-muted-foreground">Loading…</div>}
      {q.data && <EventForm mode="edit" initial={q.data} />}
    </div>
  );
}
