import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { SeverityChip } from "@/components/SeverityChip";
import type { Severity, PostEventAnalysis } from "@/lib/types";
import { toast } from "sonner";

export function PostEventForm({
  eventId,
  onSuccess,
}: {
  eventId: number;
  onSuccess?: () => void;
}) {
  const qc = useQueryClient();
  const [form, setForm] = useState({
    actual_congestion_level: "medium" as Severity,
    actual_risk_score: "",
    actual_delay_minutes: "",
    actual_crowd_size: "",
    performance_notes: "",
  });

  const submit = useMutation({
    mutationFn: async () => {
      const payload = {
        actual_congestion_level: form.actual_congestion_level,
        actual_risk_score: parseFloat(form.actual_risk_score),
        actual_delay_minutes: parseInt(form.actual_delay_minutes, 10),
        actual_crowd_size: parseInt(form.actual_crowd_size, 10),
        performance_notes: form.performance_notes || null,
      };
      return (await api.post(`/post-event/${eventId}`, payload)).data;
    },
    onSuccess: () => {
      toast.success("Analysis submitted");
      qc.invalidateQueries({ queryKey: ["post-event", String(eventId)] });
      qc.invalidateQueries({ queryKey: ["post-event-list"] });
      onSuccess?.();
    },
  });

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        submit.mutate();
      }}
      className="space-y-4"
    >
      <div className="grid md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Actual Congestion Level</Label>
          <Select
            value={form.actual_congestion_level}
            onValueChange={(v) =>
              setForm({ ...form, actual_congestion_level: v as Severity })
            }
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="low">Low</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="high">High</SelectItem>
              <SelectItem value="critical">Critical</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>Actual Risk Score</Label>
          <Input
            type="number"
            step="0.1"
            value={form.actual_risk_score}
            onChange={(e) => setForm({ ...form, actual_risk_score: e.target.value })}
            required
          />
        </div>
        <div className="space-y-2">
          <Label>Actual Delay (min)</Label>
          <Input
            type="number"
            value={form.actual_delay_minutes}
            onChange={(e) => setForm({ ...form, actual_delay_minutes: e.target.value })}
            required
          />
        </div>
        <div className="space-y-2">
          <Label>Actual Crowd Size</Label>
          <Input
            type="number"
            value={form.actual_crowd_size}
            onChange={(e) => setForm({ ...form, actual_crowd_size: e.target.value })}
            required
          />
        </div>
        <div className="space-y-2 md:col-span-2">
          <Label>Performance Notes</Label>
          <Textarea
            value={form.performance_notes}
            onChange={(e) => setForm({ ...form, performance_notes: e.target.value })}
            rows={3}
          />
        </div>
      </div>
      <Button type="submit" disabled={submit.isPending}>
        {submit.isPending ? "Submitting…" : "Submit Analysis"}
      </Button>
    </form>
  );
}

export function PostEventReport({ data }: { data: PostEventAnalysis }) {
  const rows: { label: string; pred: React.ReactNode; act: React.ReactNode }[] = [
    {
      label: "Congestion",
      pred: data.predicted_congestion_level ? (
        <SeverityChip level={data.predicted_congestion_level} />
      ) : (
        "—"
      ),
      act: <SeverityChip level={data.actual_congestion_level} />,
    },
    {
      label: "Risk Score",
      pred: data.predicted_risk_score?.toFixed?.(1) ?? "—",
      act: data.actual_risk_score?.toFixed?.(1),
    },
    {
      label: "Delay (min)",
      pred: data.predicted_delay_minutes ?? "—",
      act: data.actual_delay_minutes,
    },
  ];
  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-accent/40 p-4 rounded-md">
          <div className="text-[10px] mono uppercase text-muted-foreground">
            Prediction Accuracy
          </div>
          <div className="display text-3xl mt-1">
            {data.prediction_accuracy_pct?.toFixed?.(0) ?? "—"}%
          </div>
        </div>
        <div className="bg-accent/40 p-4 rounded-md">
          <div className="text-[10px] mono uppercase text-muted-foreground">
            Congestion Match
          </div>
          <div className="display text-3xl mt-1">{data.congestion_match ? "YES" : "NO"}</div>
        </div>
      </div>
      <table className="w-full text-sm">
        <thead className="text-xs uppercase mono text-muted-foreground">
          <tr>
            <th className="text-left py-2">Metric</th>
            <th className="text-left">Predicted</th>
            <th className="text-left">Actual</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.label} className="border-t border-border">
              <td className="py-2">{r.label}</td>
              <td className="mono">{r.pred}</td>
              <td className="mono">{r.act}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {data.improvement_recommendations && (
        <div>
          <div className="text-xs uppercase mono text-muted-foreground mb-2">
            System Recommendations
          </div>
          <p className="text-sm whitespace-pre-wrap bg-accent/30 p-3 rounded-md">
            {data.improvement_recommendations}
          </p>
        </div>
      )}
      {data.performance_notes && (
        <div>
          <div className="text-xs uppercase mono text-muted-foreground mb-2">Notes</div>
          <p className="text-sm whitespace-pre-wrap">{data.performance_notes}</p>
        </div>
      )}
    </div>
  );
}
