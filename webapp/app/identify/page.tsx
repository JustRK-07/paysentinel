"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Card, Badge, TextInput, Select, SelectItem } from "@tremor/react";
import { Search } from "lucide-react";
import { fetchCatalog, fetchAtlasHeatmap } from "@/lib/api";

const SURFACES = [
  "voice", "video", "identity", "social_engineering",
  "transaction", "agentic_commerce", "supply_chain",
];

const SEVERITIES = ["critical", "high", "medium", "low"];

export default function IdentifyPage() {
  const [items, setItems] = useState<any[]>([]);
  const [heatmap, setHeatmap] = useState<any>({});
  const [q, setQ] = useState("");
  const [surface, setSurface] = useState<string | null>(null);
  const [severity, setSeverity] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    fetchCatalog().then(setItems);
    fetchAtlasHeatmap().then(setHeatmap);
  }, []);

  const filtered = items.filter((a) => {
    if (surface && a.surface !== surface) return false;
    if (severity && a.severity !== severity) return false;
    if (q && !`${a.id} ${a.name}`.toLowerCase().includes(q.toLowerCase())) return false;
    return true;
  });

  const selectedAttack = items.find((a) => a.id === selected);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold tracking-tight">
          Identify <span className="gradient-text">Attack Catalog</span>
        </h1>
        <p className="text-fg-muted mt-1">
          30 novel GenAI-powered payment fraud vectors, grounded in real cases, mapped to MITRE ATLAS.
        </p>
      </header>

      <div className="grid grid-cols-12 gap-6">
        {/* Filters */}
        <div className="col-span-3 space-y-4">
          <Card className="glass">
            <div className="space-y-3">
              <div className="relative">
                <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-4 h-4 text-fg-muted" />
                <input
                  value={q}
                  onChange={(e) => setQ(e.target.value)}
                  placeholder="Search attacks…"
                  className="w-full rounded-md border border-border bg-surface pl-8 pr-3 py-1.5 text-sm focus:border-primary focus:outline-none"
                />
              </div>
              <div>
                <label className="text-xs uppercase tracking-wider text-fg-muted">Surface</label>
                <div className="mt-1 flex flex-wrap gap-1">
                  <Chip active={!surface} onClick={() => setSurface(null)}>all</Chip>
                  {SURFACES.map((s) => (
                    <Chip key={s} active={surface === s} onClick={() => setSurface(s)}>
                      {s.replace("_", " ")}
                    </Chip>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-xs uppercase tracking-wider text-fg-muted">Severity</label>
                <div className="mt-1 flex flex-wrap gap-1">
                  <Chip active={!severity} onClick={() => setSeverity(null)}>all</Chip>
                  {SEVERITIES.map((s) => (
                    <Chip key={s} active={severity === s} onClick={() => setSeverity(s)}>
                      {s}
                    </Chip>
                  ))}
                </div>
              </div>
            </div>
          </Card>

          {/* ATLAS heatmap */}
          <Card className="glass">
            <h3 className="text-sm font-semibold">MITRE ATLAS Heatmap</h3>
            <p className="text-xs text-fg-muted mt-1">tactic × severity</p>
            <div className="mt-3 space-y-1">
              {Object.entries(heatmap).map(([tactic, levels]: any) => (
                <div key={tactic} className="flex items-center gap-1 font-mono text-xs">
                  <span className="w-20 truncate text-fg-muted">{tactic}</span>
                  {SEVERITIES.map((sev) => {
                    const v = levels[sev] || 0;
                    const opacity = v > 0 ? 0.3 + Math.min(0.7, v * 0.2) : 0.05;
                    const bg =
                      sev === "critical" ? "bg-accent" :
                      sev === "high" ? "bg-warning" :
                      sev === "medium" ? "bg-info" : "bg-fg-muted";
                    return (
                      <div
                        key={sev}
                        className={`flex-1 h-4 rounded ${bg}`}
                        style={{ opacity }}
                        title={`${tactic} ${sev}: ${v}`}
                      />
                    );
                  })}
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Catalog */}
        <div className="col-span-5 space-y-2 max-h-[70vh] overflow-y-auto pr-2">
          {filtered.map((a, i) => (
            <motion.div
              key={a.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25, delay: 0.02 * i }}
            >
              <Card
                className={`glass cursor-pointer transition ${
                  selected === a.id ? "border-primary/60 glow-cyan" : "hover:border-border/80"
                }`}
                onClick={() => setSelected(a.id)}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs text-primary">{a.id}</span>
                      <h3 className="font-semibold truncate">{a.name}</h3>
                    </div>
                    <p className="text-xs text-fg-muted mt-1 line-clamp-2">{a.mechanics}</p>
                  </div>
                  <div className="flex flex-col gap-1 items-end shrink-0">
                    <Badge
                      color={
                        a.severity === "critical" ? "red" :
                        a.severity === "high" ? "amber" :
                        a.severity === "medium" ? "yellow" : "gray"
                      }
                      className="text-xs"
                    >
                      {a.severity}
                    </Badge>
                    <span className="text-xs text-fg-muted">{a.surface.replace("_", " ")}</span>
                  </div>
                </div>
              </Card>
            </motion.div>
          ))}
          {filtered.length === 0 && (
            <div className="text-center text-fg-muted py-12">No attacks match your filters.</div>
          )}
        </div>

        {/* Detail */}
        <div className="col-span-4">
          {selectedAttack ? (
            <motion.div
              key={selectedAttack.id}
              initial={{ opacity: 0, x: 12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3 }}
            >
              <Card className="glass">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs text-primary">{selectedAttack.id}</span>
                  <Badge color={
                    selectedAttack.severity === "critical" ? "red" :
                    selectedAttack.severity === "high" ? "amber" :
                    "yellow"
                  }>
                    {selectedAttack.severity}
                  </Badge>
                </div>
                <h2 className="text-xl font-bold mt-2">{selectedAttack.name}</h2>
                <p className="text-sm text-fg-muted mt-1">
                  {selectedAttack.surface.replace("_", " ")} · {selectedAttack.likelihood} likelihood
                </p>

                {selectedAttack.ai_brief && (
                  <div className="mt-4 rounded-md border border-info/30 bg-info/5 p-3 text-xs">
                    <div className="text-info font-semibold mb-1 flex items-center gap-1">
                      ✦ AI Brief
                    </div>
                    {selectedAttack.ai_brief}
                  </div>
                )}

                <div className="mt-4">
                  <h4 className="text-xs uppercase tracking-wider text-fg-muted">Mechanics</h4>
                  <p className="text-sm mt-1">{selectedAttack.mechanics}</p>
                </div>

                <div className="mt-4">
                  <h4 className="text-xs uppercase tracking-wider text-fg-muted">Indicators</h4>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {selectedAttack.indicators.map((i: string) => (
                      <Badge key={i} color="cyan" className="text-xs">{i}</Badge>
                    ))}
                  </div>
                </div>

                <div className="mt-4">
                  <h4 className="text-xs uppercase tracking-wider text-fg-muted">Suggested defense</h4>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {selectedAttack.suggested_defense.map((d: string) => (
                      <Badge key={d} color="emerald" className="text-xs">{d}</Badge>
                    ))}
                  </div>
                </div>
              </Card>
            </motion.div>
          ) : (
            <Card className="glass h-full flex items-center justify-center text-fg-muted text-sm">
              Select an attack to view AI brief
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

function Chip({
  active, onClick, children,
}: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={`text-xs rounded-md border px-2 py-0.5 transition ${
        active
          ? "bg-primary/10 border-primary/40 text-primary"
          : "border-border text-fg-muted hover:border-border/60 hover:text-fg"
      }`}
    >
      {children}
    </button>
  );
}
