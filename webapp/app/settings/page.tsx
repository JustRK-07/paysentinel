"use client";

import { Card, Badge, Button } from "@tremor/react";
import { Save, RefreshCw, Key, Database, Brain } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="space-y-6 max-w-3xl">
      <header>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-fg-muted mt-1">Configure the PaySentinel backend pipeline.</p>
      </header>

      <Card className="glass space-y-4">
        <Section title="LLM backend" icon={Brain}>
          <Field label="Provider" value="Anthropic" badge="cyan" />
          <Field label="Model" value="claude-sonnet-4-5" />
          <Field label="Fallback" value="template-based (deterministic)" />
        </Section>
      </Card>

      <Card className="glass space-y-4">
        <Section title="Datasets" icon={Database}>
          <Field label="Base dataset" value="PaySim" badge="cyan" />
          <Field label="Synthetic output dir" value="./data/synthetic/" />
          <Field label="Volume per attack" value="800" />
        </Section>
      </Card>

      <Card className="glass space-y-4">
        <Section title="Defense" icon={Key}>
          <Field label="Models" value="xgboost · lightgbm · gnn · transformer · llm_judge" />
          <Field label="Ensemble weights" value="0.30 · 0.25 · 0.20 · 0.15 · 0.10" />
          <Field label="Decision threshold" value="0.50" />
        </Section>
      </Card>

      <div className="flex gap-2">
        <Button icon={Save}>Save changes</Button>
        <Button icon={RefreshCw} variant="secondary">Reset to defaults</Button>
      </div>
    </div>
  );
}

function Section({
  title, icon: Icon, children,
}: { title: string; icon: any; children: React.ReactNode }) {
  return (
    <div>
      <h2 className="text-sm font-semibold mb-3 flex items-center gap-2">
        <Icon className="w-4 h-4 text-primary" />
        {title}
      </h2>
      <div className="space-y-2">{children}</div>
    </div>
  );
}

function Field({
  label, value, badge,
}: { label: string; value: string; badge?: string }) {
  return (
    <div className="flex items-center justify-between rounded-md border border-border bg-elevated px-3 py-2">
      <span className="text-xs text-fg-muted uppercase">{label}</span>
      <div className="flex items-center gap-2">
        <span className="font-mono text-sm">{value}</span>
        {badge && <Badge color={badge as any} className="text-xs">active</Badge>}
      </div>
    </div>
  );
}
