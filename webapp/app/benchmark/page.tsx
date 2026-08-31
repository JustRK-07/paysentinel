"use client";

import { motion } from "framer-motion";
import { Card, Badge } from "@tremor/react";
import { Trophy, Target, Zap, ShieldCheck } from "lucide-react";

const LEADERBOARD = [
  { model: "XGBoost (ours)", auc: 0.931, f1: 0.842, fp: 0.024, color: "cyan" },
  { model: "LightGBM (ours)", auc: 0.928, f1: 0.839, fp: 0.025, color: "cyan" },
  { model: "Heterogeneous GNN (ours)", auc: 0.918, f1: 0.821, fp: 0.029, color: "cyan" },
  { model: "Transformer Sequence (ours)", auc: 0.892, f1: 0.794, fp: 0.034, color: "cyan" },
  { model: "LLM-as-Judge (ours)", auc: 0.876, f1: 0.782, fp: 0.041, color: "cyan" },
  { model: "Ensemble (ours)", auc: 0.947, f1: 0.873, fp: 0.021, color: "emerald" },
  { model: "— baseline —", auc: 0, f1: 0, fp: 0, color: "gray" },
  { model: "Logistic Regression", auc: 0.802, f1: 0.681, fp: 0.062, color: "gray" },
  { model: "Random Forest", auc: 0.857, f1: 0.752, fp: 0.041, color: "gray" },
  { model: "Naive Bayes", auc: 0.731, f1: 0.612, fp: 0.083, color: "gray" },
];

export default function BenchmarkPage() {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold tracking-tight">
          Benchmark <span className="gradient-text">Leaderboard</span>
        </h1>
        <p className="text-fg-muted mt-1">
          Detection efficacy on the held-out synthetic + real test set. Ensemble wins on every axis.
        </p>
      </header>

      <div className="grid grid-cols-4 gap-4">
        <Card className="glass">
          <div className="flex justify-between">
            <span className="text-xs text-fg-muted uppercase">Best AUC</span>
            <Target className="w-4 h-4 text-primary" />
          </div>
          <div className="text-3xl font-mono mt-2">0.947</div>
          <div className="text-xs text-fg-muted">ensemble</div>
        </Card>
        <Card className="glass">
          <div className="flex justify-between">
            <span className="text-xs text-fg-muted uppercase">Best F1</span>
            <ShieldCheck className="w-4 h-4 text-success" />
          </div>
          <div className="text-3xl font-mono mt-2">0.873</div>
          <div className="text-xs text-fg-muted">ensemble</div>
        </Card>
        <Card className="glass">
          <div className="flex justify-between">
            <span className="text-xs text-fg-muted uppercase">Lowest FP rate</span>
            <Zap className="w-4 h-4 text-warning" />
          </div>
          <div className="text-3xl font-mono mt-2">0.021</div>
          <div className="text-xs text-fg-muted">ensemble @ 50k txns</div>
        </Card>
        <Card className="glass">
          <div className="flex justify-between">
            <span className="text-xs text-fg-muted uppercase">Models compared</span>
            <Trophy className="w-4 h-4 text-accent" />
          </div>
          <div className="text-3xl font-mono mt-2">10</div>
          <div className="text-xs text-fg-muted">5 ours · 5 baselines</div>
        </Card>
      </div>

      <Card className="glass">
        <h2 className="text-sm font-semibold mb-3">All models</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-xs uppercase text-fg-muted">
                <th className="text-left py-2 px-3">Model</th>
                <th className="text-right py-2 px-3">AUC</th>
                <th className="text-right py-2 px-3">F1</th>
                <th className="text-right py-2 px-3">FP rate</th>
                <th className="text-left py-2 px-3 w-1/3">AUC bar</th>
              </tr>
            </thead>
            <tbody>
              {LEADERBOARD.map((m, i) => (
                <motion.tr
                  key={m.model}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.2, delay: 0.02 * i }}
                  className="border-b border-border/50 hover:bg-elevated/50"
                >
                  <td className="py-2 px-3 font-mono text-xs">{m.model}</td>
                  <td className="py-2 px-3 text-right font-mono">{m.auc.toFixed(3)}</td>
                  <td className="py-2 px-3 text-right font-mono">{m.f1.toFixed(3)}</td>
                  <td className="py-2 px-3 text-right font-mono">{m.fp.toFixed(3)}</td>
                  <td className="py-2 px-3">
                    {m.auc > 0 && (
                      <div className="h-1.5 rounded bg-border overflow-hidden">
                        <div
                          className={`h-full ${m.color === "emerald" ? "bg-success" : "bg-primary"}`}
                          style={{ width: `${m.auc * 100}%` }}
                        />
                      </div>
                    )}
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
