# PaySentinel — Web Prototype

Next.js 14 dashboard for PaySentinel — agentic red-team lab for GenAI payment fraud.

## Run

```bash
npm install
npm run dev
```

Open <http://localhost:3000>.

## Pages

- `/` — Dashboard (live KPIs, score stream, recent attacks)
- `/identify` — Attack catalog browser with MITRE ATLAS heatmap
- `/generate` — Synthetic fraud generation control
- `/defend` — Real-time scoring table + ensemble health
- `/loop` — Closed-loop iteration visualizer
- `/benchmark` — Leaderboard across all models

## Theme

Cyber-noir dark — `electric cyan (#00E5FF) + hot magenta (#FF006E) + emerald (#10B981) + electric purple (#A78BFA)` on near-black `#0A0A0F`. Subtle grid background, glow accents.

## Stack

- **Next.js 14** with App Router
- **TypeScript** strict
- **Tailwind CSS** with custom theme tokens
- **shadcn/ui-style primitives** (Radix-based, copied in)
- **Tremor** for charts + KPI cards
- **TanStack Table + Virtual** for the live transaction feed
- **Framer Motion** for animations
- **lucide-react** icons

## Backend integration

The frontend talks to the FastAPI scoring service (`http://localhost:8000`) and the
Identify pillar service (`http://localhost:8001`). Both are auto-fallback to mock data so
the prototype renders something useful even when the backend isn't running.

## Mock data

`lib/mock-data.ts` — when the backend isn't reachable, the UI shows realistic mock data so
demoing never breaks.
