import { createFileRoute } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send, Bot, User, Sparkles } from "lucide-react";
import type { CopilotMessage } from "@/lib/types";
import { formatIST } from "@/lib/utils";
import { toast } from "sonner";

export const Route = createFileRoute("/_app/copilot")({
  component: CopilotPage,
});

function CopilotPage() {
  const qc = useQueryClient();
  const [q, setQ] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const history = useQuery({
    queryKey: ["copilot-history"],
    queryFn: async () =>
      (await api.get<CopilotMessage[]>("/copilot/history")).data,
  });

  const ask = useMutation({
    mutationFn: async (query: string) =>
      (await api.post("/copilot/ask", { query })).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["copilot-history"] });
      setQ("");
    },
    onError: () => toast.error("Copilot request failed"),
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history.data, ask.isPending]);

  const handleKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (q.trim() && !ask.isPending) ask.mutate(q.trim());
    }
  };

  // Reverse so oldest messages appear first (chronological)
  const items = [...(history.data ?? [])].reverse();

  return (
    <div className="flex flex-col h-[calc(100dvh-56px)] lg:h-dvh">
      {/* ── Header ── */}
      <div className="flex items-center gap-3 px-6 py-4 border-b border-border shrink-0 bg-card/60 backdrop-blur-sm">
        <div className="h-9 w-9 rounded-lg bg-primary/20 flex items-center justify-center">
          <Sparkles className="h-5 w-5 text-primary" />
        </div>
        <div>
          <h1 className="display text-lg leading-none">AI Copilot</h1>
          <p className="text-[11px] text-muted-foreground mt-0.5 mono">
            Powered by Gemini · Operational intelligence assistant
          </p>
        </div>
      </div>

      {/* ── Messages ── */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6 min-h-0">
        {/* Empty state */}
        {!history.isLoading && items.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-4 text-center">
            <div className="h-16 w-16 rounded-2xl bg-primary/10 flex items-center justify-center">
              <Bot className="h-8 w-8 text-primary" />
            </div>
            <div>
              <p className="font-semibold text-lg">Ask the Copilot</p>
              <p className="text-sm text-muted-foreground mt-1 max-w-xs">
                Ask anything about traffic, events, predictions, resource
                allocation, or operational recommendations.
              </p>
            </div>
            <div className="flex flex-wrap gap-2 justify-center mt-2">
              {[
                "What events are high risk today?",
                "Summarise current traffic situation",
                "How many officers are deployed?",
              ].map((s) => (
                <button
                  key={s}
                  onClick={() => setQ(s)}
                  className="text-xs bg-accent hover:bg-accent/80 transition-colors px-3 py-1.5 rounded-full border border-border text-muted-foreground"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {history.isLoading && (
          <div className="flex justify-center py-10 text-muted-foreground text-sm">
            Loading history…
          </div>
        )}

        {/* Message bubbles */}
        {items.map((m, i) => (
          <div key={m.query_id ?? i} className="space-y-3 max-w-3xl mx-auto w-full">
            {/* Timestamp row */}
            <div className="flex items-center gap-2">
              <div className="flex-1 h-px bg-border" />
              <span className="text-[10px] mono text-muted-foreground whitespace-nowrap">
                {m.created_at
                  ? formatIST(m.created_at, "MMM d, HH:mm")
                  : ""}
                {m.event_id != null && ` · Event #${m.event_id}`}
              </span>
              <div className="flex-1 h-px bg-border" />
            </div>

            {/* User message */}
            <div className="flex items-start gap-3 justify-end">
              <div className="bg-primary text-primary-foreground px-4 py-2.5 rounded-2xl rounded-tr-sm text-sm max-w-[80%] leading-relaxed">
                {m.user_query}
              </div>
              <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
                <User className="h-4 w-4 text-primary" />
              </div>
            </div>

            {/* AI response */}
            <div className="flex items-start gap-3">
              <div className="h-8 w-8 rounded-full bg-route-blue/20 flex items-center justify-center shrink-0">
                <Bot className="h-4 w-4 text-route-blue" />
              </div>
              <div className="bg-card border border-border px-4 py-3 rounded-2xl rounded-tl-sm text-sm max-w-[80%] leading-relaxed text-foreground/90 copilot-prose">
                <ReactMarkdown
                  components={{
                    p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                    ul: ({ children }) => <ul className="list-disc pl-4 mb-2 space-y-1">{children}</ul>,
                    ol: ({ children }) => <ol className="list-decimal pl-4 mb-2 space-y-1">{children}</ol>,
                    li: ({ children }) => <li className="leading-relaxed">{children}</li>,
                    strong: ({ children }) => <strong className="font-semibold text-foreground">{children}</strong>,
                    em: ({ children }) => <em className="italic">{children}</em>,
                    h1: ({ children }) => <h1 className="text-base font-bold mb-1 mt-2 first:mt-0">{children}</h1>,
                    h2: ({ children }) => <h2 className="text-sm font-bold mb-1 mt-2 first:mt-0">{children}</h2>,
                    h3: ({ children }) => <h3 className="text-sm font-semibold mb-1 mt-2 first:mt-0">{children}</h3>,
                    code: ({ children }) => <code className="bg-accent/60 px-1 py-0.5 rounded text-xs mono">{children}</code>,
                    blockquote: ({ children }) => <blockquote className="border-l-2 border-primary/40 pl-3 italic text-muted-foreground my-1">{children}</blockquote>,
                    hr: () => <hr className="border-border my-2" />,
                  }}
                >
                  {m.gemini_response ?? ""}
                </ReactMarkdown>
              </div>
            </div>
          </div>
        ))}

        {/* Pending indicator */}
        {ask.isPending && (
          <div className="flex items-start gap-3 max-w-3xl mx-auto w-full">
            <div className="h-8 w-8 rounded-full bg-route-blue/20 flex items-center justify-center shrink-0">
              <Bot className="h-4 w-4 text-route-blue" />
            </div>
            <div className="bg-card border border-border px-4 py-3 rounded-2xl rounded-tl-sm">
              <div className="flex gap-1.5 items-center h-5">
                <span className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce [animation-delay:0ms]" />
                <span className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce [animation-delay:150ms]" />
                <span className="h-2 w-2 rounded-full bg-muted-foreground animate-bounce [animation-delay:300ms]" />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* ── Input bar ── */}
      <div className="shrink-0 border-t border-border bg-card/60 backdrop-blur-sm px-4 py-3">
        <div className="max-w-3xl mx-auto flex gap-3 items-end">
          <Textarea
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Ask anything… (Enter to send, Shift+Enter for new line)"
            rows={2}
            className="resize-none flex-1 bg-accent/40 border-border focus:border-primary transition-colors"
          />
          <Button
            onClick={() => { if (q.trim()) ask.mutate(q.trim()); }}
            disabled={ask.isPending || !q.trim()}
            size="icon"
            className="h-11 w-11 shrink-0"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
        <p className="text-[10px] mono text-muted-foreground text-center mt-2">
          Responses are AI-generated and may not always be accurate.
        </p>
      </div>
    </div>
  );
}
