"use client";

import { motion } from "framer-motion";
import { ReactNode } from "react";

// ============================================================
// SKELETON — Loading placeholders that match content layout
// ============================================================

export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div
      className={`animate-pulse rounded-md bg-gradient-to-r from-elevated via-border/40 to-elevated bg-[length:200%_100%] ${className}`}
      style={{ animation: "shimmer 2s linear infinite" }}
    />
  );
}

export function SkeletonRow({ cols = 5 }: { cols?: number }) {
  return (
    <div className="flex items-center gap-3 py-2 px-3 border-b border-border/50">
      {Array.from({ length: cols }).map((_, i) => (
        <Skeleton
          key={i}
          className={`h-4 ${i === 0 ? "w-24" : i === cols - 1 ? "w-16 ml-auto" : "flex-1"}`}
        />
      ))}
    </div>
  );
}

export function SkeletonTable({ rows = 5, cols = 5 }: { rows?: number; cols?: number }) {
  return (
    <div className="space-y-0">
      <div className="flex items-center gap-3 py-2 px-3 border-b border-border">
        {Array.from({ length: cols }).map((_, i) => (
          <Skeleton key={i} className={`h-3 ${i === 0 ? "w-20" : "flex-1"}`} />
        ))}
      </div>
      {Array.from({ length: rows }).map((_, i) => (
        <SkeletonRow key={i} cols={cols} />
      ))}
    </div>
  );
}

export function SkeletonCard() {
  return (
    <div className="rounded-md border border-border bg-surface p-4 space-y-2">
      <Skeleton className="h-3 w-20" />
      <Skeleton className="h-8 w-24" />
      <Skeleton className="h-3 w-32" />
    </div>
  );
}

// ============================================================
// EMPTY STATE — Friendly message + CTA when no data
// ============================================================

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon?: any;
  title: string;
  description: string;
  action?: { label: string; onClick: () => void };
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="flex flex-col items-center justify-center text-center py-12 px-6"
    >
      {Icon && (
        <div className="w-12 h-12 rounded-full bg-primary/10 border border-primary/30 flex items-center justify-center mb-3">
          <Icon className="w-5 h-5 text-primary" />
        </div>
      )}
      <h3 className="text-sm font-semibold text-fg">{title}</h3>
      <p className="text-xs text-fg-muted mt-1 max-w-sm">{description}</p>
      {action && (
        <button
          onClick={action.onClick}
          className="mt-4 rounded-md border border-primary/40 bg-primary/10 px-3 py-1.5 text-xs font-medium text-primary hover:bg-primary/20 transition"
        >
          {action.label}
        </button>
      )}
    </motion.div>
  );
}

// ============================================================
// SCORE GAUGE — Animated circular progress
// ============================================================

export function ScoreGauge({
  score,
  decision,
  size = 160,
}: {
  score: number; // 0..1
  decision: string;
  size?: number;
}) {
  const radius = (size - 16) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - Math.min(1, Math.max(0, score)));

  const color =
    score >= 0.7 ? "#FF006E" : score >= 0.5 ? "#F59E0B" : "#10B981";

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="rgba(31, 34, 48, 0.6)"
          strokeWidth="8"
          fill="none"
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth="8"
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.2, ease: "easeOut" }}
          style={{ filter: `drop-shadow(0 0 6px ${color})` }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="font-mono text-2xl font-bold" style={{ color }}>
          {(score * 100).toFixed(1)}
        </div>
        <div className="text-xs text-fg-muted uppercase tracking-wider mt-0.5">
          {decision}
        </div>
      </div>
    </div>
  );
}

// ============================================================
// TOOLTIP — Hover info on metric tiles
// ============================================================

import { useState } from "react";
import { HelpCircle } from "lucide-react";

export function MetricTooltip({ text }: { text: string }) {
  const [open, setOpen] = useState(false);
  return (
    <span
      className="relative inline-flex items-center ml-1 cursor-help"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <HelpCircle className="w-3 h-3 text-fg-muted hover:text-fg transition" />
      {open && (
        <motion.div
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.15 }}
          className="absolute z-50 left-1/2 -translate-x-1/2 top-full mt-2 w-56 rounded-md border border-border bg-elevated/95 backdrop-blur px-3 py-2 text-xs text-fg shadow-xl"
        >
          {text}
          <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-2 h-2 rotate-45 bg-elevated border-l border-t border-border" />
        </motion.div>
      )}
    </span>
  );
}

// ============================================================
// KBD SHORTCUT HINT — Subtle keyboard shortcut badge
// ============================================================

export function Kbd({ children }: { children: ReactNode }) {
  return (
    <kbd className="inline-flex items-center justify-center min-w-[1.5rem] px-1.5 h-5 rounded border border-border bg-elevated font-mono text-[10px] text-fg-muted">
      {children}
    </kbd>
  );
}
