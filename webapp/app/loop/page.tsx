"use client";

import { motion } from "framer-motion";
import { Card, LineChart, Badge } from "@tremor/react";
import { mockIterations } from "@/lib/mock-data";
import { TrendingUp, Repeat, ArrowRight } from "lucide-react";

export default function LoopPage() {
  const data = mockIterations.map((it, i) => ({
    iter: `Iter ${it.iteration}`,
    AUC: it.blended_auc,
    F1: it.blended_f1,
    "FP rate": it.blended_fp_rate * 10, // rescale for visibility
  }));

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold tracking-tight">
          Closed Loop <span className="gradient-text">Feedback Engine</span>
        </h1>
        <p className="text-fg-muted mt-1">
          Generate → Defend → failure analysis → re-Generate. Each round, the defender's misses become the
          seed corpus for the next round of attacks.
        </p>
      </header>

      {/* Loop diagram */}
      <Card className="glass">
        <div className="flex items-center justify-between gap-2 font-mono text-xs">
          <Node color="cyan" label="Identify" sub="30 vectors" />
          <Arrow />
          <Node color="info" label="Generate" sub="5,840 sims" />
          <Arrow />
          <Node color="warning" label="Defend" sub="ensemble" />
          <Arrow />
          <Node color="accent" label="Failure analysis" sub="top-K missed" />
          <Arrow />
          <Node color="success" label="Re-seed" sub="new attacks" />
        </div>
        <div className="mt-3 text-xs text-fg-muted text-center">
          ↺ each iteration improves detection AUC and reduces false-positive rate
        </div>
      </Card>

      {/* AUC progression */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="glass col-span-2">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold">Iteration metrics progression</h2>
            <TrendingUp className="w-4 h-4 text-success" />
          </div>
          <LineChart
            className="mt-4 h-64"
            data={data}
            index="iter"
            categories={["AUC", "F1", "FP rate"]}
            colors={["cyan", "emerald", "magenta"]}
            showLegend
            showAnimation
          />
        </Card>

        <Card className="glass">
          <h2 className="text-sm font-semibold">Final state</h2>
          <div className="mt-4 space-y-3">
            <Stat label="Final AUC" value="0.947" delta="+0.083" />
            <Stat label="Final F1" value="0.873" delta="+0.092" />
            <Stat label="FP rate" value="0.021" delta="-0.012" />
            <Stat label="Training set" value="28,400" sub="txns" />
          </div>
        </Card>
      </div>

      {/* Per-iteration breakdown */}
      <Card className="glass">
        <h2 className="text-sm font-semibold mb-3">Iteration breakdown</h2>
        <div className="space-y-3">
          {mockIterations.map((it, i) => (
            <motion.div
              key={it.iteration}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: 0.05 * i }}
              className="grid grid-cols-12 items-center gap-3 rounded-md border border-border bg-elevated px-4 py-3"
            >
              <div className="col-span-1">
                <Badge color="cyan" className="text-xs">#{it.iteration}</Badge>
              </div>
              <div className="col-span-2 font-mono text-xs">AUC {it.blended_auc.toFixed(3)}</div>
              <div className="col-span-2 font-mono text-xs">F1 {it.blended_f1.toFixed(3)}</div>
              <div className="col-span-2 font-mono text-xs">FP {it.blended_fp_rate.toFixed(3)}</div>
              <div className="col-span-2 font-mono text-xs text-fg-muted">{it.n_train.toLocaleString()} train</div>
              <div className="col-span-3 flex flex-wrap gap-1 justify-end">
                {it.new_seeds.map((s) => (
                  <Badge key={s} color="magenta" className="text-xs">{s}</Badge>
                ))}
              </div>
            </motion.div>
          ))}
        </div>
      </Card>
    </div>
  );
}

function Node({ color, label, sub }: { color: string; label: string; sub: string }) {
  const colors: Record<string, string> = {
    cyan: "border-primary/40 bg-primary/10 text-primary",
    info: "border-info/40 bg-info/10 text-info",
    warning: "border-warning/40 bg-warning/10 text-warning",
    accent: "border-accent/40 bg-accent/10 text-accent",
    success: "border-success/40 bg-success/10 text-success",
  };
  return (
    <div className={`flex-1 rounded-md border ${colors[color]} px-3 py-2 text-center`}>
      <div className="font-semibold">{label}</div>
      <div className="text-xs opacity-70 mt-0.5">{sub}</div>
    </div>
  );
}
function Arrow() {
  return <ArrowRight className="w-4 h-4 text-fg-muted shrink-0" />;
}
function Stat({ label, value, delta, sub }: { label: string; value: string; delta?: string; sub?: string }) {
  return (
    <div className="flex items-center justify-between rounded-md border border-border bg-elevated px-3 py-2">
      <span className="text-xs text-fg-muted uppercase">{label}</span>
      <div className="flex items-center gap-2">
        <span className="font-mono">{value}</span>
        {delta && <Badge color={delta.startsWith("+") ? "emerald" : "red"} className="text-xs">{delta}</Badge>}
        {sub && <span className="text-xs text-fg-muted">{sub}</span>}
      </div>
    </div>
  );
}
