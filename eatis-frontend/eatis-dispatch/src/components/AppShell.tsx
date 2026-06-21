import { Link, useRouterState, Outlet } from "@tanstack/react-router";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";
import { useState, useEffect } from "react";
import {
  LayoutDashboard,
  CalendarRange,
  Map,
  FlaskConical,
  BarChart3,
  ClipboardCheck,
  Bot,
  User as UserIcon,
  LogOut,
  UserPlus,
  Menu,
  X,
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, roles: null },
  { to: "/events", label: "Events", icon: CalendarRange, roles: null },
  { to: "/map", label: "City Map", icon: Map, roles: null },
  { to: "/simulator", label: "Simulator", icon: FlaskConical, roles: null },
  {
    to: "/analytics",
    label: "Analytics",
    icon: BarChart3,
    roles: ["analyst", "operator", "admin"],
  },
  { to: "/post-event", label: "Post-Event", icon: ClipboardCheck, roles: null },
  { to: "/copilot", label: "Copilot", icon: Bot, roles: null },
  { to: "/users/create", label: "Create User", icon: UserPlus, roles: ["admin"] },
] as const;

function SidebarContent({
  onNavClick,
}: {
  onNavClick?: () => void;
}) {
  const { user, logout } = useAuth();
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  return (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-sidebar-border">
        <div className="flex items-center gap-2">
          <div className="h-9 w-9 rounded-md bg-primary text-primary-foreground flex items-center justify-center font-display font-bold">
            E
          </div>
          <div>
            <div className="display text-lg leading-none">EATIS</div>
            <div className="text-[10px] uppercase tracking-widest text-muted-foreground mono mt-1">
              Dispatch
            </div>
          </div>
        </div>
      </div>

      {/* Nav items */}
      <nav className="flex-1 px-2 py-3 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          if (item.roles && user && !item.roles.includes(user.role as never)) return null;
          const active = pathname === item.to || pathname.startsWith(item.to + "/");
          const Icon = item.icon;
          return (
            <Link
              key={item.to}
              to={item.to}
              onClick={onNavClick}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                active
                  ? "bg-primary/15 text-primary border-l-2 border-primary"
                  : "text-sidebar-foreground hover:bg-sidebar-accent",
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span className="display tracking-wide uppercase text-xs">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* User profile */}
      <div className="p-3 border-t border-sidebar-border">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="w-full justify-start gap-2 h-auto py-2">
              <div className="h-7 w-7 rounded-full bg-accent flex items-center justify-center text-xs font-semibold shrink-0">
                {user?.name?.[0]?.toUpperCase() ?? "?"}
              </div>
              <div className="text-left flex-1 min-w-0">
                <div className="text-xs truncate">{user?.name}</div>
                <div className="text-[10px] uppercase mono text-muted-foreground">
                  {user?.role}
                </div>
              </div>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuLabel className="mono text-xs">{user?.email}</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link to="/profile" onClick={onNavClick}>
                <UserIcon className="h-4 w-4 mr-2" /> Profile
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem onClick={logout}>
              <LogOut className="h-4 w-4 mr-2" /> Logout
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
}

export function AppShell() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  // Close mobile nav whenever route changes
  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  // Prevent body scroll when mobile menu is open
  useEffect(() => {
    if (mobileOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileOpen]);

  return (
    <div className="min-h-screen flex w-full bg-background text-foreground">
      {/* ── Desktop sidebar (lg and above) ──────────────────────── */}
      <aside className="hidden lg:flex w-60 shrink-0 bg-sidebar border-r border-sidebar-border flex-col">
        <SidebarContent />
      </aside>

      {/* ── Mobile overlay backdrop ──────────────────────────────── */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* ── Mobile drawer ────────────────────────────────────────── */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-72 bg-sidebar border-r border-sidebar-border flex flex-col transition-transform duration-300 ease-in-out lg:hidden",
          mobileOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        {/* Close button inside drawer */}
        <button
          onClick={() => setMobileOpen(false)}
          className="absolute top-4 right-4 text-muted-foreground hover:text-foreground transition-colors"
          aria-label="Close menu"
        >
          <X className="h-5 w-5" />
        </button>
        <SidebarContent onNavClick={() => setMobileOpen(false)} />
      </aside>

      {/* ── Main content area ────────────────────────────────────── */}
      <div className="flex-1 min-w-0 flex flex-col overflow-x-hidden">
        {/* Mobile top bar (hamburger) */}
        <header className="lg:hidden sticky top-0 z-30 flex items-center gap-3 px-4 py-3 bg-sidebar border-b border-sidebar-border">
          <button
            onClick={() => setMobileOpen(true)}
            className="text-sidebar-foreground hover:text-foreground transition-colors"
            aria-label="Open menu"
          >
            <Menu className="h-6 w-6" />
          </button>
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-md bg-primary text-primary-foreground flex items-center justify-center font-display font-bold text-sm">
              E
            </div>
            <span className="display text-base uppercase tracking-wide leading-none">EATIS</span>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 min-w-0">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-start gap-3 sm:gap-4 mb-6">
      <div className="flex-1 min-w-0">
        <h1 className="display text-2xl sm:text-3xl uppercase tracking-wide leading-tight">{title}</h1>
        {subtitle && <p className="text-sm text-muted-foreground mt-1 break-words">{subtitle}</p>}
      </div>
      {actions && (
        <div className="flex flex-wrap gap-2 shrink-0">{actions}</div>
      )}
    </div>
  );
}
