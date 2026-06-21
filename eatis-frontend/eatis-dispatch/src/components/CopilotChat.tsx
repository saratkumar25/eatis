import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send } from "lucide-react";
import { toast } from "sonner";

interface Msg {
  role: "user" | "assistant";
  content: string;
}

export default function CopilotChat({ eventId }: { eventId?: number }) {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const ask = useMutation({
    mutationFn: async (query: string) => {
      // Backend returns CopilotResponse: { query_id, user_query, gemini_response, event_id, created_at }
      const { data } = await api.post<{ gemini_response: string }>("/copilot/ask", {
        query,
        event_id: eventId ?? null,
      });
      return data.gemini_response;
    },
    onSuccess: (response) => {
      setMessages((m) => [...m, { role: "assistant", content: response ?? "(no response)" }]);
    },
    onError: () => {
      toast.error("Copilot request failed");
      setMessages((m) => [...m, { role: "assistant", content: "Sorry, something went wrong. Please try again." }]);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const q = input.trim();
    if (!q) return;
    setMessages((m) => [...m, { role: "user", content: q }]);
    setInput("");
    ask.mutate(q);
  };

  const handleKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as unknown as React.FormEvent);
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-0 mt-4">
      <div className="flex-1 overflow-y-auto space-y-3 pr-1">
        {messages.length === 0 && (
          <p className="text-sm text-muted-foreground">
            Ask anything about traffic, events, predictions, or recommendations.
          </p>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={
              m.role === "user"
                ? "bg-primary/15 border-l-2 border-primary p-3 rounded-md text-sm"
                : "bg-card border border-border p-3 rounded-md text-sm copilot-prose"
            }
          >
            {m.role === "assistant" ? (
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
                {m.content}
              </ReactMarkdown>
            ) : (
              m.content
            )}
          </div>
        ))}
        {ask.isPending && (
          <div className="text-xs text-muted-foreground mono animate-pulse">Thinking…</div>
        )}
        <div ref={bottomRef} />
      </div>
      <form onSubmit={handleSubmit} className="mt-3 flex gap-2 border-t border-border pt-3">
        <Textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Ask the copilot…"
          rows={2}
          className="resize-none"
        />
        <Button type="submit" disabled={ask.isPending || !input.trim()} size="icon">
          <Send className="h-4 w-4" />
        </Button>
      </form>
    </div>
  );
}
