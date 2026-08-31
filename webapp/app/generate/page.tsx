"use client";

import { motion } from "framer-motion";
import { Card, Badge, Button } from "@tremor/react";
import { Wand2, Mic, FileText, User, Bot } from "lucide-react";
import { useState } from "react";

const GENERATORS = [
  { key: "phishing_email", label: "Phishing emails", icon: FileText, count: 50, color: "text-accent" },
  { key: "scam_call_script", label: "Scam call scripts", icon: Mic, count: 30, color: "text-warning" },
  { key: "synthetic_identity", label: "Synthetic identities", icon: User, count: 40, color: "text-info" },
  { key: "kyc_document", label: "KYC documents", icon: FileText, count: 40, color: "text-primary" },
  { key: "agent_trajectory", label: "Agent trajectories", icon: Bot, count: 30, color: "text-success" },
];

export default function GeneratePage() {
  const [running, setRunning] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  const runGen = (key: string) => {
    setRunning(key);
    setProgress(0);
    const id = setInterval(() => {
      setProgress((p) => {
        if (p >= 100) {
          clearInterval(id);
          setRunning(null);
          return 100;
        }
        return p + 8;
      });
    }, 120);
  };

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold tracking-tight">
          Generate <span className="gradient-text">Synthetic Fraud</span>
        </h1>
        <p className="text-fg-muted mt-1">
          Multi-model synthesis — CTGAN + TabDDPM for transactions, LLM agents for narrative artifacts.
          Validated on a 3-axis fidelity harness.
        </p>
      </header>

      <div className="grid grid-cols-3 gap-4">
        {GENERATORS.map((g, i) => (
          <motion.div
            key={g.key}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.05 * i }}
          >
            <Card className="glass">
              <div className="flex items-start justify-between">
                <g.icon className={`w-6 h-6 ${g.color}`} />
                <Badge color="cyan" className="text-xs">
                  {g.count} / batch
                </Badge>
              </div>
              <h3 className="font-semibold mt-3">{g.label}</h3>
              <p className="text-xs text-fg-muted mt-1">
                Source: Anthropic Sonnet 4.5 + template fallback
              </p>
              <div className="mt-4">
                <Button
                  icon={Wand2}
                  onClick={() => runGen(g.key)}
                  loading={running === g.key}
                  className="w-full"
                >
                  {running === g.key ? `Generating… ${progress}%` : "Run generator"}
                </Button>
                {running === g.key && (
                  <div className="mt-2 h-1 bg-border rounded overflow-hidden">
                    <motion.div
                      className="h-full bg-primary"
                      animate={{ width: `${progress}%` }}
                      transition={{ duration: 0.1 }}
                    />
                  </div>
                )}
              </div>
            </Card>
          </motion.div>
        ))}
      </div>

      <Card className="glass">
        <h2 className="text-sm font-semibold mb-3">Last fidelity report</h2>
        <div className="grid grid-cols-4 gap-4">
          <Metric label="Statistical" value="0.78" sub="KS + Wasserstein" />
          <Metric label="Behavioral" value="0.71" sub="smurfing + mule-flow" />
          <Metric label="Task-level" value="0.83" sub="detector transfer AUC" />
          <Metric label="Overall" value="0.77" sub="weighted blend" accent />
        </div>
        <div className="mt-4 text-xs text-fg-muted">
          Three-axis fidelity harness addresses the gap noted in <em>Synthetic Tabular Generators Fail to
          Preserve Behavioral Fraud Patterns</em> (arXiv 2604.13125).
        </div>
      </Card>
    </div>
  );
}

function Metric({
  label, value, sub, accent,
}: { label: string; value: string; sub: string; accent?: boolean }) {
  return (
    <div className={`rounded-md border p-3 ${accent ? "border-primary/40 bg-primary/5" : "border-border bg-elevated"}`}>
      <div className="text-xs text-fg-muted uppercase">{label}</div>
      <div className={`text-2xl font-mono mt-1 ${accent ? "text-primary" : ""}`}>{value}</div>
      <div className="text-xs text-fg-muted mt-1">{sub}</div>
    </div>
  );
}
