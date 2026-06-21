import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { PageHeader } from "@/components/AppShell";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { AxiosError } from "axios";

export const Route = createFileRoute("/_app/profile")({
  component: ProfilePage,
});

function ProfilePage() {
  const { user } = useAuth();
  const [form, setForm] = useState({ current_password: "", new_password: "" });

  const change = useMutation({
    mutationFn: async () => (await api.post("/auth/change-password", form)).data,
    onSuccess: () => {
      toast.success("Password updated");
      setForm({ current_password: "", new_password: "" });
    },
    onError: (err) => {
      const detail =
        err instanceof AxiosError ? (err.response?.data?.detail ?? err.message) : "Failed";
      toast.error(typeof detail === "string" ? detail : "Failed");
    },
  });

  return (
    <div className="p-6 lg:p-8 max-w-2xl space-y-6">
      <PageHeader title="Profile" />
      <Card className="p-5 space-y-3">
        <Field label="Name" value={user?.name ?? ""} />
        <Field label="Email" value={user?.email ?? ""} />
        <Field label="Role" value={user?.role ?? ""} />
      </Card>

      <Card className="p-5">
        <div className="display uppercase text-sm tracking-widest text-muted-foreground mb-4">
          Change Password
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            change.mutate();
          }}
          className="space-y-4"
        >
          <div className="space-y-2">
            <Label>Current Password</Label>
            <Input
              type="password"
              value={form.current_password}
              onChange={(e) => setForm({ ...form, current_password: e.target.value })}
              required
            />
          </div>
          <div className="space-y-2">
            <Label>New Password</Label>
            <Input
              type="password"
              value={form.new_password}
              onChange={(e) => setForm({ ...form, new_password: e.target.value })}
              required
              minLength={6}
            />
          </div>
          <Button type="submit" disabled={change.isPending}>
            {change.isPending ? "Updating…" : "Update Password"}
          </Button>
        </form>
      </Card>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid grid-cols-3 gap-2 items-center">
      <div className="text-xs uppercase mono text-muted-foreground">{label}</div>
      <div className="col-span-2 mono text-sm">{value}</div>
    </div>
  );
}
