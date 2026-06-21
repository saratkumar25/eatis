import { lazy, Suspense, useState, type ReactNode } from "react";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { MessageSquare } from "lucide-react";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";

const CopilotChat = lazy(() => import("./CopilotChat"));

interface CopilotState {
  eventId?: number;
  eventLabel?: string;
}

let openFn: ((state?: CopilotState) => void) | null = null;
export const openCopilot = (s?: CopilotState) => openFn?.(s);

export function CopilotLauncher() {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const [state, setState] = useState<CopilotState>({});

  openFn = (s) => {
    setState(s ?? {});
    setOpen(true);
  };

  if (!user) return null;

  return (
    <>
      <Button
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 z-50 shadow-lg rounded-full h-14 w-14 p-0"
        aria-label="Ask EATIS AI"
      >
        <MessageSquare className="h-6 w-6" />
      </Button>
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetContent className="w-full sm:max-w-lg flex flex-col">
          <SheetHeader>
            <SheetTitle className="display">EATIS AI</SheetTitle>
            {state.eventLabel && (
              <p className="text-xs text-muted-foreground mono">
                Context: event #{state.eventId} — {state.eventLabel}
              </p>
            )}
          </SheetHeader>
          <Suspense fallback={<div className="p-4 text-sm">Loading...</div>}>
            <CopilotChat eventId={state.eventId} />
          </Suspense>
        </SheetContent>
      </Sheet>
    </>
  );
}

export function CopilotProvider({ children }: { children: ReactNode }) {
  return (
    <>
      {children}
      <CopilotLauncher />
    </>
  );
}
