"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { AreaChart, Card, Metric, Text, Badge, Grid, Flex, SparkAreaChart, Button } from "@tremor/react";
import { Activity, AlertTriangle, Cpu, Shield, Zap, TrendingUp, Crosshair } from "lucide-react";
import { mockKpis, mockScoreStream, mockRecentAttacks } from "@/lib/mock-data";
import { MetricTooltip } from "@/components/ui-states";
import { toast } from "@/components/toast";

export default function DashboardPage() {
  const [demoing, setDemoing] = useState(false);
  const [demoResult, setDemoResult] = useState<null | {
    txn_id: string;
    score: number;
    decision: string;
    top_feature: string;
    amount: number;
  }>(null);

  const runSampleFraud = async () => {
    setDemoing(true);
    try {
      const base = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8002";
      // High-velocity large transfer from a freshly-opened account → typical money-laundering pattern
      const txn = {
        step: Math.floor(Math.random() * 168),
        type: "TRANSFER",
        amount: 87_500,
        nameOrig: `C${Math.floor(Math.random() * 999_999)}`,
        oldbalanceOrg: 87_500,
        newbalanceOrig: 0,
        nameDest: `M${Math.floor(Math.random() * 9999)}`,
        oldbalanceDest: 0,
        newbalanceDest: 87_500,
      };
      const r = await fetch(`${base}/score`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transactions: [txn] }),
      });
      if (!r.ok) throw new Error(`API ${r.status}`);
      const j = await r.json();
      const first = j?.predictions?.[0];
      if (first) {
        setDemoResult({
          txn_id: first.txn_id ?? txn.nameOrig,
          score: first.score ?? 0,
          decision: first.decision ?? "review",
          top_feature: first.top_feature ?? "amount",
          amount: txn.amount,
        });
        toast({
          title: `Result: ${first.decision?.toUpperCase() ?? "?"} · score ${(first.score ?? 0).toFixed(3)}`,
          description: `${first.txn_id ?? txn.nameOrig} · $${txn.amount.toLocaleString()}`,
          variant: first.decision === "block" ? "critical" : first.decision === "review" ? "warning" : "success",
        });
      } else {
        throw new Error("Empty prediction");
      }
    } catch (e: any) {
      // Realistic synthetic fallback when API isn't running — shows the full decision flow
      const fallback = {
        txn_id: `T-${Math.floor(Math.random() * 999_999).toString().padStart(6, "0")}-0`,
        score: 0.847,
        decision: "review",
        top_feature: "amount_velocity_ratio",
        amount: 87_500,
      };
      setDemoResult(fallback);
      toast({
        title: `Demo result · ${fallback.score.toFixed(3)} (review)`,
        description: "API offline · showing synthetic demo result. Start the Defend API for live scoring.",
        variant: "warning",
      });
    }
    setDemoing(false);
  };
  return (
    <div className="space-y-8">
      {/* Hero */}
      <header className="space-y-3">
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="flex items-center gap-3"
        >
          <Badge color="cyan" className="bg-primary/10 text-primary border-primary/30">
            <span className="w-2 h-2 bg-primary rounded-full mr-2 animate-pulse-glow" />
            Live
          </Badge>
          <span className="text-xs text-fg-muted font-mono">iteration 3 / 3 · closed-loop active</span>
        </motion.div>
        <h1 className="text-4xl font-bold tracking-tight">
          PaySentinel <span className="gradient-text">Agentic Red-Team Lab</span>
        </h1>
        <p className="text-fg-muted max-w-2xl">
          Identify novel GenAI payment fraud attacks, generate realistic simulations at scale,
          defend with an ensemble detector — all in one closed feedback loop.
        </p>
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <Button
            icon={Crosshair}
            onClick={runSampleFraud}
            loading={demoing}
            className="shadow-[0_0_24px_-6px_rgba(0,229,255,0.6)]"
          >
            Try a sample fraud detection
          </Button>
          <span className="text-xs text-fg-muted font-mono">
            submits $87.5k TRANSFER → ensemble scores it
          </span>
        </div>
        {demoResult && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-3 inline-flex items-center gap-3 rounded-md border border-border bg-elevated px-3 py-2"
          >
            <Shield className={`w-4 h-4 ${demoResult.decision === "block" ? "text-accent" : demoResult.decision === "review" ? "text-warning" : "text-success"}`} />
            <span className="font-mono text-xs">{demoResult.txn_id}</span>
            <span className="text-xs text-fg-muted">·</span>
            <span className="font-mono text-xs">${demoResult.amount.toLocaleString()}</span>
            <span className="text-xs text-fg-muted">·</span>
            <span className="font-mono text-xs">score {demoResult.score.toFixed(3)}</span>
            <Badge color={demoResult.decision === "block" ? "red" : demoResult.decision === "review" ? "amber" : "emerald"} className="text-xs">
              {demoResult.decision}
            </Badge>
            <span className="text-xs text-fg-muted">· top feature:</span>
            <span className="font-mono text-xs text-info">{demoResult.top_feature}</span>
          </motion.div>
        )}
      </header>

      {/* KPI tiles with sparklines */}
      <Grid numItems={4} className="gap-4">
        {mockKpis.map((k, i) => (
          <motion.div
            key={k.label}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.05 * i }}
          >
            <Card className="glass">
              <Flex>
                <Text className="text-fg-muted text-xs uppercase tracking-wider flex items-center">
                  {k.label}
                  <MetricTooltip text={k.tooltip} />
                </Text>
                <k.icon className={`w-4 h-4 ${k.color}`} />
              </Flex>
              <Metric className="mt-2 font-mono">{k.value}</Metric>
              <div className="h-8 mt-1">
                <SparkAreaChart
                  data={k.sparkData}
                  index="t"
                  categories={[k.sparkKey]}
                  colors={[k.sparkColor]}
                  showGradient
                  className="h-full"
                />
              </div>
              <Flex className="mt-1">
                <Text className="text-xs text-fg-muted">{k.sub}</Text>
                {k.delta && (
                  <Badge color={k.delta.startsWith("+") ? "emerald" : "red"} className="text-xs">
                    {k.delta}
                  </Badge>
                )}
              </Flex>
            </Card>
          </motion.div>
        ))}
      </Grid>

      {/* Live score stream + recent attacks */}
      <Grid numItems={3} className="gap-4">
        <div className="col-span-2">
          <Card className="glass">
            <Flex>
              <div>
                <Text className="text-fg-muted text-xs uppercase tracking-wider">Live fraud-score stream</Text>
                <Text className="text-xs text-fg-muted">rolling 60s · all active channels</Text>
              </div>
              <Activity className="w-4 h-4 text-primary animate-pulse" />
            </Flex>
            <AreaChart
              className="mt-4 h-64"
              data={mockScoreStream}
              index="t"
              categories={["score", "threshold"]}
              colors={["cyan", "magenta"]}
              showLegend={false}
              showGradient
            />
          </Card>
        </div>

        <Card className="glass">
          <Flex>
            <Text className="text-fg-muted text-xs uppercase tracking-wider">Recent attacks</Text>
            <AlertTriangle className="w-4 h-4 text-accent" />
          </Flex>
          <ul className="mt-3 space-y-2">
            {mockRecentAttacks.map((a, i) => (
              <motion.li
                key={a.id}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: 0.03 * i }}
                className="flex items-center justify-between rounded-md border border-border bg-elevated px-3 py-2"
              >
                <div className="flex items-center gap-2 min-w-0">
                  <span className="font-mono text-xs text-primary shrink-0">{a.id}</span>
                  <span className="text-xs truncate">{a.name}</span>
                </div>
                <Badge
                  color={a.severity === "critical" ? "red" : a.severity === "high" ? "amber" : "yellow"}
                  className="text-xs shrink-0"
                >
                  {a.severity}
                </Badge>
              </motion.li>
            ))}
          </ul>
        </Card>
      </Grid>

      {/* System status row */}
      <Grid numItems={3} className="gap-4">
        <Card className="glass">
          <Flex>
            <Text className="text-fg-muted text-xs uppercase tracking-wider">Models</Text>
            <Cpu className="w-4 h-4 text-info" />
          </Flex>
          <ul className="mt-3 space-y-1 font-mono text-xs">
            <li className="flex justify-between"><span>xgboost</span><span className="text-success">● live</span></li>
            <li className="flex justify-between"><span>lightgbm</span><span className="text-success">● live</span></li>
            <li className="flex justify-between"><span>heterogeneous_gnn</span><span className="text-success">● live</span></li>
            <li className="flex justify-between"><span>transformer_sequence</span><span className="text-success">● live</span></li>
            <li className="flex justify-between"><span>llm_judge</span><span className="text-success">● live</span></li>
          </ul>
        </Card>
        <Card className="glass">
          <Flex>
            <Text className="text-fg-muted text-xs uppercase tracking-wider flex items-center">
              Detection latency
              <MetricTooltip text="99th percentile scoring latency across all ensemble members." />
            </Text>
            <Zap className="w-4 h-4 text-warning" />
          </Flex>
          <div className="text-3xl font-mono mt-2">38<span className="text-sm text-fg-muted ml-1">ms</span></div>
          <div className="h-8 mt-2">
            <SparkAreaChart
              data={Array.from({ length: 20 }, (_, i) => ({ t: i, latency: 30 + Math.sin(i / 3) * 8 + Math.random() * 4 }))}
              index="t"
              categories={["latency"]}
              colors={["amber"]}
              showGradient
              className="h-full"
            />
          </div>
          <Text className="text-xs text-fg-muted mt-1">p99 · target &lt; 50ms</Text>
        </Card>
        <Card className="glass">
          <Flex>
            <Text className="text-fg-muted text-xs uppercase tracking-wider">AUC progression</Text>
            <TrendingUp className="w-4 h-4 text-success" />
          </Flex>
          <Metric className="mt-2 font-mono">0.947</Metric>
          <div className="h-8 mt-1">
            <SparkAreaChart
              data={[
                { t: 1, auc: 0.864 },
                { t: 2, auc: 0.921 },
                { t: 3, auc: 0.947 },
              ]}
              index="t"
              categories={["auc"]}
              colors={["emerald"]}
              showGradient
              className="h-full"
            />
          </div>
          <Text className="text-xs text-fg-muted">+0.083 over 3 iterations</Text>
        </Card>
      </Grid>
    </div>
  );
}
