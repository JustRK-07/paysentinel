"use client";

import { Search, Bell, Github } from "lucide-react";
import { motion } from "framer-motion";

export function TopBar() {
  return (
    <motion.header
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="fixed top-0 left-0 right-0 h-16 border-b border-border bg-background/80 backdrop-blur z-30 flex items-center justify-between px-6"
    >
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-md bg-gradient-to-br from-primary to-accent flex items-center justify-center font-bold text-sm">
          P
        </div>
        <span className="font-semibold tracking-tight">PaySentinel</span>
        <span className="text-xs text-fg-muted font-mono">/ Agentic Red-Team Lab</span>
      </div>

      <div className="flex items-center gap-3 flex-1 max-w-md mx-8">
        <div className="relative w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-fg-muted" />
          <input
            type="text"
            placeholder="Search attacks, models, metrics…"
            className="w-full rounded-md border border-border bg-surface pl-9 pr-3 py-1.5 text-sm placeholder:text-fg-muted focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/30"
          />
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button className="rounded-md border border-border bg-surface px-3 py-1.5 text-sm hover:bg-elevated transition">
          <Github className="w-4 h-4 inline mr-2" />
          Repo
        </button>
        <button className="rounded-md p-2 hover:bg-elevated transition relative">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-accent rounded-full animate-pulse-glow" />
        </button>
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-info to-primary" />
      </div>
    </motion.header>
  );
}
