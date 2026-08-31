"use client";

import { motion } from "framer-motion";
import { AreaChart, Card, Metric, Text, Badge, Grid, Flex } from "@tremor/react";
import { Activity, AlertTriangle, Cpu, Shield, Zap, TrendingUp } from "lucide-react";
import { mockKpis, mockScoreStream, mockRecentAttacks } from "@/lib/mock-data";

export default function DashboardPage() {
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
      </header>

      {/* KPI tiles */}
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
                <Text className="text-fg-muted text-xs uppercase tracking-wider">{k.label}</Text>
                <k.icon className={`w-4 h-4 ${k.color}`} />
              </Flex>
              <Metric className="mt-2 font-mono">{k.value}</Metric>
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
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs text-primary">{a.id}</span>
                  <span className="text-xs">{a.name}</span>
                </div>
                <Badge
                  color={a.severity === "critical" ? "red" : a.severity === "high" ? "amber" : "yellow"}
                  className="text-xs"
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
            <Text className="text-fg-muted text-xs uppercase tracking-wider">Detection latency</Text>
            <Zap className="w-4 h-4 text-warning" />
          </Flex>
          <Metric className="mt-2 font-mono">38<span className="text-sm text-fg-muted ml-1">ms</span></Metric>
          <Text className="text-xs text-fg-muted">p99 · target &lt; 50ms</Text>
        </Card>
        <Card className="glass">
          <Flex>
            <Text className="text-fg-muted text-xs uppercase tracking-wider">AUC progression</Text>
            <TrendingUp className="w-4 h-4 text-success" />
          </Flex>
          <Metric className="mt-2 font-mono">0.947</Metric>
          <Text className="text-xs text-fg-muted">+0.083 over 3 iterations</Text>
        </Card>
      </Grid>
    </div>
  );
}
