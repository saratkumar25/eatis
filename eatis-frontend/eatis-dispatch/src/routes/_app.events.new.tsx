import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/AppShell";
import { EventForm } from "@/components/EventForm";
import type { EventItem } from "@/lib/types";

export const Route = createFileRoute("/_app/events/new")({
  component: NewEventPage,
});

function NewEventPage() {
  const search =
    typeof window !== "undefined" ? new URLSearchParams(window.location.search) : null;

  const prefill: Partial<EventItem> | undefined = search?.get("event_type")
    ? {
        name: search.get("name") ?? undefined,
        description: search.get("description") ?? undefined,
        event_type: (search.get("event_type") ?? undefined) as EventItem["event_type"],
        location_name: search.get("location_name") ?? undefined,
        address: search.get("address") ?? undefined,
        latitude: search.get("latitude") ? parseFloat(search.get("latitude")!) : undefined,
        longitude: search.get("longitude") ? parseFloat(search.get("longitude")!) : undefined,
        start_datetime: search.get("start_datetime") ?? undefined,
        end_datetime: search.get("end_datetime") ?? undefined,
        expected_crowd_size: search.get("expected_crowd_size")
          ? parseInt(search.get("expected_crowd_size")!, 10)
          : undefined,
        has_road_closure: search.get("road_closure") === "true",
        road_closure_details: search.get("road_closure_details") ?? undefined,
      }
    : undefined;

  return (
    <div className="p-6 lg:p-8 max-w-4xl">
      <PageHeader
        title="New Event"
        subtitle={
          prefill
            ? "Pre-filled from simulation — review and complete the remaining fields"
            : "Create a new event for traffic analysis"
        }
      />
      <EventForm mode="create" initial={prefill} />
    </div>
  );
}
