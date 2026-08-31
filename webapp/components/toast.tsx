"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, Shield, X } from "lucide-react";

export type Toast = {
  id: string;
  title: string;
  description?: string;
  variant: "critical" | "warning" | "info" | "success";
  duration?: number;
};

let listeners: ((toast: Toast) => void)[] = [];

export function toast(t: Omit<Toast, "id">) {
  const id = Math.random().toString(36).slice(2);
  listeners.forEach((l) => l({ ...t, id }));
}

export function ToastHost() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  useEffect(() => {
    const fn = (t: Toast) => {
      setToasts((prev) => [...prev, t]);
      const dur = t.duration ?? 4000;
      setTimeout(() => {
        setToasts((prev) => prev.filter((p) => p.id !== t.id));
      }, dur);
    };
    listeners.push(fn);
    return () => {
      listeners = listeners.filter((l) => l !== fn);
    };
  }, []);

  const dismiss = (id: string) => setToasts((p) => p.filter((t) => t.id !== id));

  return (
    <div className="fixed top-20 right-4 z-50 space-y-2 w-80 pointer-events-none">
      <AnimatePresence>
        {toasts.map((t) => (
          <motion.div
            key={t.id}
            initial={{ opacity: 0, x: 20, scale: 0.95 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 20, scale: 0.95 }}
            transition={{ duration: 0.25 }}
            className={`pointer-events-auto rounded-md border backdrop-blur-xl px-3 py-2 shadow-2xl ${
              t.variant === "critical"
                ? "border-accent/40 bg-accent/10"
                : t.variant === "warning"
                ? "border-warning/40 bg-warning/10"
                : t.variant === "success"
                ? "border-success/40 bg-success/10"
                : "border-info/40 bg-info/10"
            }`}
          >
            <div className="flex items-start gap-2">
              {t.variant === "critical" ? (
                <AlertTriangle className="w-4 h-4 text-accent shrink-0 mt-0.5" />
              ) : t.variant === "warning" ? (
                <AlertTriangle className="w-4 h-4 text-warning shrink-0 mt-0.5" />
              ) : t.variant === "success" ? (
                <Shield className="w-4 h-4 text-success shrink-0 mt-0.5" />
              ) : (
                <Shield className="w-4 h-4 text-info shrink-0 mt-0.5" />
              )}
              <div className="flex-1 min-w-0">
                <div className="text-xs font-semibold">{t.title}</div>
                {t.description && (
                  <div className="text-xs text-fg-muted mt-0.5">{t.description}</div>
                )}
              </div>
              <button
                onClick={() => dismiss(t.id)}
                className="text-fg-muted hover:text-fg shrink-0"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
