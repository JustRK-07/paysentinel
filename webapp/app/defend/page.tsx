"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Card, Badge, Button } from "@tremor/react";
import { Activity, Zap, ShieldCheck, AlertOctagon, Upload } from "lucide-react";
import { mockLiveScoring } from "@/lib/mock-data";

export default function DefendPage() {
  const [rows, setRows] = useState(mockLiveScoring);
  const [scoring, setScoring] = useState(false);

  const scoreNew = () => {
    setScoring(true);
    setTimeout(() => {
      setRows((prev) =>
        [
          {
            txn: `T-${Math.floor(Math.random() * 90000 + 10000)}`,
            amount: Math.round(Math.random() * 50000 * 100) / 100,
            score: Math.random(),
            decision: ["approve", "approve", "review", "block"][Math.floor(Math.random() * 4)],
            top_feature: ["drain_flag", "transfer_only_flag", "small_amount_velocity"][Math.floor(Math.random() * 3)],
          },
          ...prev,
        ].slice(0, 30)
      );
      setScoring(false);
    }, 600);
  };

  return (
    <div className="space-y-6">
      <header className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Defend <span className="gradient-text">Live Scoring</span>
          </h1>
          <p className="text-fg-muted mt-1">
            Real-time ensemble: XGBoost · LightGBM · GNN · Transformer · LLM-Judge.
          </p>
        </div>
        <div className="flex gap-2">
          <Button icon={Upload} variant="secondary">Upload CSV</Button>
          <Button onClick={scoreNew} loading={scoring} icon={Zap}>
            Score batch
          </Button>
        </div>
      </header>

      {/* Live metrics row */}
      <div className="grid grid-cols-4 gap-4">
        <Card className="glass">
          <div className="flex justify-between">
            <span className="text-xs text-fg-muted uppercase">Scored / sec</span>
            <Activity className="w-4 h-4 text-primary" />
          </div>
          <div className="text-3xl font-mono mt-2">412</div>
          <div className="text-xs text-success">▲ 38 vs avg</div>
        </Card>
        <Card className="glass">
          <div className="flex justify-between">
            <span className="text-xs text-fg-muted uppercase">p99 latency</span>
            <Zap className="w-4 h-4 text-warning" />
          </div>
          <div className="text-3xl font-mono mt-2">38<span className="text-base text-fg-muted">ms</span></div>
          <div className="text-xs text-success">▼ 12ms target hit</div>
        </Card>
        <Card className="glass">
          <div className="flex justify-between">
            <span className="text-xs text-fg-muted uppercase">Live F1</span>
            <ShieldCheck className="w-4 h-4 text-success" />
          </div>
          <div className="text-3xl font-mono mt-2">0.873</div>
          <div className="text-xs text-success">▲ 0.083 since iter 1</div>
        </Card>
        <Card className="glass">
          <div className="flex justify-between">
            <span className="text-xs text-fg-muted uppercase">False positive rate</span>
            <AlertOctagon className="w-4 h-4 text-accent" />
          </div>
          <div className="text-3xl font-mono mt-2">0.021</div>
          <div className="text-xs text-success">▼ 0.012 since iter 1</div>
        </Card>
      </div>

      {/* Live scoring table */}
      <Card className="glass">
        <h2 className="text-sm font-semibold mb-3">Live transaction scores</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-xs uppercase text-fg-muted">
                <th className="text-left py-2 px-3">Txn</th>
                <th className="text-right py-2 px-3">Amount</th>
                <th className="text-left py-2 px-3">Score</th>
                <th className="text-left py-2 px-3">Decision</th>
                <th className="text-left py-2 px-3">Top feature</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <motion.tr
                  key={`${r.txn}-${i}`}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.2 }}
                  className="border-b border-border/50 hover:bg-elevated/50"
                >
                  <td className="py-2 px-3 font-mono text-xs">{r.txn}</td>
                  <td className="py-2 px-3 text-right font-mono">${r.amount.toLocaleString()}</td>
                  <td className="py-2 px-3">
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-1.5 rounded bg-border overflow-hidden">
                        <div
                          className={`h-full ${
                            r.score > 0.7 ? "bg-accent" : r.score > 0.5 ? "bg-warning" : "bg-success"
                          }`}
                          style={{ width: `${r.score * 100}%` }}
                        />
                      </div>
                      <span className="font-mono text-xs">{r.score.toFixed(3)}</span>
                    </div>
                  </td>
                  <td className="py-2 px-3">
                    <Badge
                      color={
                        r.decision === "block" ? "red" :
                        r.decision === "review" ? "amber" : "emerald"
                      }
                      className="text-xs"
                    >
                      {r.decision}
                    </Badge>
                  </td>
                  <td className="py-2 px-3 font-mono text-xs text-info">{r.top_feature}</td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
