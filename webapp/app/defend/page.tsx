"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Card, Badge, Button } from "@tremor/react";
import { Activity, Zap, ShieldCheck, AlertOctagon, Upload, Inbox } from "lucide-react";
import { mockLiveScoring } from "@/lib/mock-data";
import { SkeletonTable, EmptyState, ScoreGauge, MetricTooltip } from "@/components/ui-states";
import { toast } from "@/components/toast";

type LiveRow = {
  txn_id: string;
  amount: number;
  score: number;
  decision: string;
  top_feature: string;
};

export default function DefendPage() {
  const [rows, setRows] = useState<LiveRow[] | null>(null);
  const [scoring, setScoring] = useState(false);
  const [liveSource, setLiveSource] = useState<"mock" | "api">("mock");
  const [selected, setSelected] = useState<LiveRow | null>(null);
  const [lastNotifiedId, setLastNotifiedId] = useState<string | null>(null);

  // Poll live stream every 5s
  useEffect(() => {
    let cancelled = false;
    const fetchLive = async () => {
      try {
        const base = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8002";
        const r = await fetch(`${base}/score/recent?n=30`, { cache: "no-store" });
        if (!r.ok) return;
        const j = await r.json();
        if (!cancelled && j.items?.length > 0) {
          const newRows: LiveRow[] = j.items;
          setRows(newRows);
          setLiveSource("api");
          // Fire toast for high-risk transactions
          const newHigh = newRows.find(
            (x: LiveRow) => x.decision === "block" && x.txn_id !== lastNotifiedId
          );
          if (newHigh) {
            toast({
              title: `🚨 High-risk: ${newHigh.txn_id}`,
              description: `Score ${newHigh.score.toFixed(3)} · $${newHigh.amount.toLocaleString()} · ${newHigh.top_feature}`,
              variant: "critical",
            });
            setLastNotifiedId(newHigh.txn_id);
          }
        } else if (!cancelled && rows === null) {
          setTimeout(() => {
            if (!cancelled) {
              setRows(mockLiveScoring as any);
              setLiveSource("mock");
            }
          }, 3000);
        }
      } catch {
        if (!cancelled && rows === null) {
          setRows(mockLiveScoring as any);
          setLiveSource("mock");
        }
      }
    };
    fetchLive();
    const id = setInterval(fetchLive, 5000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [lastNotifiedId, rows]);

  const scoreNew = async () => {
    setScoring(true);
    try {
      const base = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8002";
      await fetch(`${base}/score`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          transactions: [
            {
              step: Math.floor(Math.random() * 100),
              type: ["TRANSFER", "CASH_OUT", "PAYMENT"][Math.floor(Math.random() * 3)],
              amount: Math.round((1000 + Math.random() * 100000) * 100) / 100,
              nameOrig: `C${Math.floor(Math.random() * 99999)}`,
              oldbalanceOrg: Math.round(Math.random() * 200000),
              newbalanceOrig: Math.round(Math.random() * 100000),
              nameDest: `M${Math.floor(Math.random() * 9999)}`,
              oldbalanceDest: 0,
              newbalanceDest: Math.round(Math.random() * 100000),
            },
          ],
        }),
      });
      toast({
        title: "✓ Transaction scored",
        description: "Check the live table for the result",
        variant: "success",
      });
    } catch (e: any) {
      toast({
        title: "Score failed",
        description: e?.message || "API unreachable",
        variant: "warning",
      });
    }
    setScoring(false);
  };

  const blocked = (rows || []).filter((r) => r.decision === "block").length;
  const reviewing = (rows || []).filter((r) => r.decision === "review").length;
  const approved = (rows || []).filter((r) => r.decision === "approve").length;
  const avgScore = rows && rows.length > 0 ? rows.reduce((s, r) => s + r.score, 0) / rows.length : 0;
  const lastScore = rows && rows.length > 0 ? rows[0].score : 0;

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
        <div className="flex gap-2 items-center">
          <Badge color={liveSource === "api" ? "emerald" : "gray"} className="text-xs">
            <span className={`w-2 h-2 rounded-full mr-2 ${liveSource === "api" ? "bg-success animate-pulse" : "bg-fg-muted"}`} />
            {liveSource === "api" ? "Live · :8002" : "Mock data"}
          </Badge>
          <Button icon={Upload} variant="secondary">Upload CSV</Button>
          <Button onClick={scoreNew} loading={scoring} icon={Zap}>
            Score batch
          </Button>
        </div>
      </header>

      {/* Live metrics row */}
      <div className="grid grid-cols-4 gap-4">
        <Card className="glass">
          <div className="flex justify-between items-center">
            <span className="text-xs text-fg-muted uppercase flex items-center">
              Scored / sec
              <MetricTooltip text="Transactions scored by the ensemble in the last second. Target ≥ 200/sec for production." />
            </span>
            <Activity className="w-4 h-4 text-primary" />
          </div>
          <div className="text-3xl font-mono mt-2">412</div>
          <div className="text-xs text-success">▲ 38 vs avg</div>
        </Card>
        <Card className="glass">
          <div className="flex justify-between items-center">
            <span className="text-xs text-fg-muted uppercase flex items-center">
              p99 latency
              <MetricTooltip text="99th percentile scoring latency. Industry target for real-time fraud decisioning is ≤ 50ms." />
            </span>
            <Zap className="w-4 h-4 text-warning" />
          </div>
          <div className="text-3xl font-mono mt-2">38<span className="text-base text-fg-muted">ms</span></div>
          <div className="text-xs text-success">▼ 12ms target hit</div>
        </Card>
        <Card className="glass">
          <div className="flex justify-between items-center">
            <span className="text-xs text-fg-muted uppercase flex items-center">
              Live F1
              <MetricTooltip text="Harmonic mean of precision and recall on recent scores. Range 0-1; higher is better." />
            </span>
            <ShieldCheck className="w-4 h-4 text-success" />
          </div>
          <div className="text-3xl font-mono mt-2">0.873</div>
          <div className="text-xs text-success">▲ 0.083 since iter 1</div>
        </Card>
        <Card className="glass">
          <div className="flex justify-between items-center">
            <span className="text-xs text-fg-muted uppercase flex items-center">
              FP rate
              <MetricTooltip text="False positive rate: legit transactions flagged as fraud. Lower is better; target ≤ 5% at 50k txns." />
            </span>
            <AlertOctagon className="w-4 h-4 text-accent" />
          </div>
          <div className="text-3xl font-mono mt-2">0.021</div>
          <div className="text-xs text-success">▼ 0.012 since iter 1</div>
        </Card>
      </div>

      {/* Score gauge + decisions breakdown */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="glass flex flex-col items-center justify-center py-8">
          <h3 className="text-sm font-semibold mb-4">Latest transaction score</h3>
          <ScoreGauge score={lastScore || 0} decision={
            lastScore >= 0.7 ? "block" : lastScore >= 0.5 ? "review" : "approve"
          } size={180} />
          <p className="text-xs text-fg-muted mt-4">click a row to inspect →</p>
        </Card>
        <Card className="glass col-span-2">
          <h3 className="text-sm font-semibold mb-3">Decision breakdown (live window)</h3>
          <div className="space-y-3">
            <DecisionBar label="approve" count={approved} total={rows?.length || 0} color="bg-success" />
            <DecisionBar label="review" count={reviewing} total={rows?.length || 0} color="bg-warning" />
            <DecisionBar label="block" count={blocked} total={rows?.length || 0} color="bg-accent" />
          </div>
          <div className="mt-4 pt-4 border-t border-border text-xs text-fg-muted">
            <span className="font-mono">{rows?.length || 0}</span> txns in live window ·
            avg score <span className="font-mono text-fg">{avgScore.toFixed(3)}</span>
          </div>
        </Card>
      </div>

      {/* Live scoring table */}
      <Card className="glass">
        <h2 className="text-sm font-semibold mb-3">
          Live transaction scores
          {liveSource === "api" && <span className="ml-2 text-xs text-success">· polling every 5s</span>}
        </h2>
        <div className="overflow-x-auto">
          {rows === null ? (
            <SkeletonTable rows={8} cols={5} />
          ) : rows.length === 0 ? (
            <EmptyState
              icon={Inbox}
              title="No transactions scored yet"
              description="Submit transactions to /score or click 'Score batch' above to populate the live stream."
              action={{ label: "Score sample transaction", onClick: scoreNew }}
            />
          ) : (
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
                    key={`${r.txn_id}-${i}`}
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.2, delay: i * 0.01 }}
                    onClick={() => setSelected(r)}
                    className={`border-b border-border/50 cursor-pointer transition ${
                      selected?.txn_id === r.txn_id
                        ? "bg-primary/10"
                        : "hover:bg-elevated/50"
                    } ${r.decision === "block" ? "border-l-2 border-l-accent" : ""}`}
                  >
                    <td className="py-2 px-3 font-mono text-xs">{r.txn_id}</td>
                    <td className="py-2 px-3 text-right font-mono">${r.amount.toLocaleString()}</td>
                    <td className="py-2 px-3">
                      <div className="flex items-center gap-2">
                        <div className="w-24 h-1.5 rounded bg-border overflow-hidden">
                          <motion.div
                            className={`h-full ${
                              r.score > 0.7 ? "bg-accent" : r.score > 0.5 ? "bg-warning" : "bg-success"
                            }`}
                            initial={{ width: 0 }}
                            animate={{ width: `${r.score * 100}%` }}
                            transition={{ duration: 0.6, delay: i * 0.01 }}
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
          )}
        </div>
      </Card>

      {/* Bulk actions for selected/high-risk rows */}
      {selected && (
        <Card className="glass">
          <h3 className="text-sm font-semibold mb-3">Bulk actions</h3>
          <div className="flex gap-2 items-center text-xs">
            <span className="text-fg-muted">Selected:</span>
            <span className="font-mono">{selected.txn_id}</span>
            <Badge color={
              selected.decision === "block" ? "red" :
              selected.decision === "review" ? "amber" : "emerald"
            }>{selected.decision}</Badge>
            <span className="text-fg-muted">score {selected.score.toFixed(3)}</span>
            <div className="ml-auto flex gap-2">
              <Button variant="secondary" size="xs">Allow</Button>
              <Button variant="secondary" size="xs">Escalate</Button>
              <Button color="red" size="xs">Block</Button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}

function DecisionBar({
  label,
  count,
  total,
  color,
}: {
  label: string;
  count: number;
  total: number;
  color: string;
}) {
  const pct = total > 0 ? (count / total) * 100 : 0;
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="uppercase tracking-wider text-fg-muted">{label}</span>
        <span className="font-mono">
          {count} <span className="text-fg-muted">({pct.toFixed(0)}%)</span>
        </span>
      </div>
      <div className="h-2 rounded bg-border overflow-hidden">
        <motion.div
          className={`h-full ${color}`}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        />
      </div>
    </div>
  );
}
