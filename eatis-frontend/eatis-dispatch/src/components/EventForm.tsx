import { useState, useEffect } from "react";
import { useNavigate } from "@tanstack/react-router";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toISTInputValue } from "@/lib/utils";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Card } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import type { EventItem } from "@/lib/types";
import { AxiosError } from "axios";

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

type FormState = {
  name: string;
  description: string;
  event_type: string;
  location_name: string;
  address: string;
  latitude: string;
  longitude: string;
  start_datetime: string;
  end_datetime: string;
  expected_crowd_size: string;
  road_closure: boolean;
  road_closure_details: string;
};

const emptyForm: FormState = {
  name: "",
  description: "",
  event_type: "political_rally",
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

interface Props {
  initial?: Partial<EventItem> & { id?: number };
  mode: "create" | "edit";
}

export function EventForm({ initial, mode }: Props) {
  const nav = useNavigate();
  const qc = useQueryClient();
  const [form, setForm] = useState<FormState>(emptyForm);

  useEffect(() => {
    if (!initial) return;
    setForm({
      name: initial.name ?? "",
      description: initial.description ?? "",
      event_type: initial.event_type ?? "political_rally",
      location_name: initial.location_name ?? "",
      address: initial.address ?? "",
      latitude: initial.latitude != null ? String(initial.latitude) : "",
      longitude: initial.longitude != null ? String(initial.longitude) : "",
      start_datetime: toISTInputValue(initial.start_datetime),
      end_datetime: toISTInputValue(initial.end_datetime),
      expected_crowd_size:
        initial.expected_crowd_size != null ? String(initial.expected_crowd_size) : "",
      road_closure: !!initial.has_road_closure,
      road_closure_details: initial.road_closure_details ?? "",
    });
  }, [initial]);

  const mutation = useMutation({
    mutationFn: async () => {
      const payload = {
        name: form.name,
        description: form.description || null,
        event_type: form.event_type,
        location_name: form.location_name,
        address: form.address || null,
        latitude: parseFloat(form.latitude),
        longitude: parseFloat(form.longitude),
        start_datetime: new Date(form.start_datetime).toISOString(),
        end_datetime: new Date(form.end_datetime).toISOString(),
        expected_crowd_size: parseInt(form.expected_crowd_size, 10),
        has_road_closure: form.road_closure,
        road_closure_details: form.road_closure ? form.road_closure_details || null : null,
      };
      if (mode === "create") {
        const { data } = await api.post<EventItem>("/events", payload);
        return data;
      }
      const { data } = await api.patch<EventItem>(`/events/${initial!.id}`, payload);
      return data;
    },
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["events"] });
      qc.invalidateQueries({ queryKey: ["event", data.id] });
      toast.success(mode === "create" ? "Event created" : "Event updated");
      nav({ to: "/events/$id", params: { id: String(data.id) } });
    },
    onError: (err) => {
      const message =
        err instanceof AxiosError ? (err.response?.data?.detail ?? err.message) : "Failed";
      toast.error(typeof message === "string" ? message : "Submission failed");
    },
  });

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (new Date(form.end_datetime) <= new Date(form.start_datetime)) {
      toast.error("End must be after start");
      return;
    }
    mutation.mutate();
  };

  return (
    <Card className="p-6">
      <form onSubmit={submit} className="space-y-5">
        <div className="grid md:grid-cols-2 gap-4">
          <div className="space-y-2 md:col-span-2">
            <Label>Event Name</Label>
            <Input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
            />
          </div>
          <div className="space-y-2 md:col-span-2">
            <Label>Description</Label>
            <Textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              rows={2}
            />
          </div>
          <div className="space-y-2">
            <Label>Event Type</Label>
            <Select
              value={form.event_type}
              onValueChange={(v) => setForm({ ...form, event_type: v })}
            >
              <SelectTrigger>
                <SelectValue />
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
            <Label>Expected Crowd Size</Label>
            <Input
              type="number"
              min="0"
              value={form.expected_crowd_size}
              onChange={(e) => setForm({ ...form, expected_crowd_size: e.target.value })}
              required
            />
          </div>
          <div className="space-y-2">
            <Label>Location Name</Label>
            <Input
              value={form.location_name}
              onChange={(e) => setForm({ ...form, location_name: e.target.value })}
              required
            />
          </div>
          <div className="space-y-2">
            <Label>Address</Label>
            <Input
              value={form.address}
              onChange={(e) => setForm({ ...form, address: e.target.value })}
            />
          </div>
          <div className="space-y-2">
            <Label>Latitude</Label>
            <Input
              type="number"
              step="any"
              value={form.latitude}
              onChange={(e) => setForm({ ...form, latitude: e.target.value })}
              required
            />
          </div>
          <div className="space-y-2">
            <Label>Longitude</Label>
            <Input
              type="number"
              step="any"
              value={form.longitude}
              onChange={(e) => setForm({ ...form, longitude: e.target.value })}
              required
            />
          </div>
          <div className="space-y-2">
            <Label>Start Date/Time</Label>
            <Input
              type="datetime-local"
              value={form.start_datetime}
              onChange={(e) => setForm({ ...form, start_datetime: e.target.value })}
              required
            />
          </div>
          <div className="space-y-2">
            <Label>End Date/Time</Label>
            <Input
              type="datetime-local"
              value={form.end_datetime}
              onChange={(e) => setForm({ ...form, end_datetime: e.target.value })}
              required
            />
          </div>
          <div className="md:col-span-2 flex items-center gap-3">
            <Switch
              id="closure"
              checked={form.road_closure}
              onCheckedChange={(v) => setForm({ ...form, road_closure: v })}
            />
            <Label htmlFor="closure">Road closure required</Label>
          </div>
          {form.road_closure && (
            <div className="md:col-span-2 space-y-2">
              <Label>Closure Details</Label>
              <Textarea
                value={form.road_closure_details}
                onChange={(e) => setForm({ ...form, road_closure_details: e.target.value })}
                rows={2}
              />
            </div>
          )}
        </div>
        <div className="flex justify-end gap-2 border-t border-border pt-4">
          <Button type="button" variant="outline" onClick={() => nav({ to: "/events" })}>
            Cancel
          </Button>
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? "Saving…" : mode === "create" ? "Create Event" : "Save Changes"}
          </Button>
        </div>
      </form>
    </Card>
  );
}
