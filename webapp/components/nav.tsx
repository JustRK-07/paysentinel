"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Radar,
  Wand2,
  ShieldCheck,
  Repeat,
  Trophy,
  Settings,
} from "lucide-react";

const NAV = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/identify", label: "Identify", icon: Radar },
  { href: "/generate", label: "Generate", icon: Wand2 },
  { href: "/defend", label: "Defend", icon: ShieldCheck },
  { href: "/loop", label: "Closed Loop", icon: Repeat },
  { href: "/benchmark", label: "Benchmark", icon: Trophy },
];

export function Nav() {
  const pathname = usePathname();
  return (
    <nav className="fixed left-0 top-16 h-[calc(100vh-4rem)] w-56 border-r border-border bg-surface/60 backdrop-blur z-20 px-3 py-6">
      <ul className="space-y-1">
        {NAV.map((item) => {
          const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <li key={item.href}>
              <Link
                href={item.href}
                className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm transition ${
                  active
                    ? "bg-primary/10 text-primary border border-primary/30"
                    : "text-fg-muted hover:text-fg hover:bg-elevated"
                }`}
              >
                <item.icon className="w-4 h-4" />
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>

      <div className="absolute bottom-6 left-3 right-3">
        <Link
          href="/settings"
          className="flex items-center gap-3 rounded-md px-3 py-2 text-sm text-fg-muted hover:text-fg hover:bg-elevated"
        >
          <Settings className="w-4 h-4" />
          Settings
        </Link>
        <div className="mt-3 rounded-md border border-border bg-elevated p-3 font-mono text-xs text-fg-muted">
          <div className="text-primary">v0.1.0 · build {new Date().toISOString().slice(0, 10)}</div>
          <div>env: dev</div>
        </div>
      </div>
    </nav>
  );
}
