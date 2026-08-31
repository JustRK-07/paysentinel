# PaySentinel — Solution Document

**An Agentic Red-Team Lab for GenAI-Powered Payment Fraud.**

Identify novel fraud attacks → generate realistic simulations → defend with an ensemble detector — all in one closed feedback loop.

---

## 1. Problem Statement

GenAI has changed the economics of payment fraud. What used to require coordination, language skill, or social-engineering talent is now automated, personalized, and produced at machine speed. Real-world cases from 2024–2026 make the gap clear:

| Attack | Case | Impact |
|---|---|---|
| CFO voice deepfake | Arup engineering firm, Hong Kong | **$25M wire fraud** in a single video call |
| Executive deepfake video | Ferrari CEO scam | attempted wire fraud |
| Synthetic identity stitching | Federal Reserve / IDology | **80% of new credit-card losses** |
| LLM spear phishing | industry-wide | 4× higher click rate than mass phishing |
| Rogue AI shopping agents | Incode 2026 report | new fraud surface as agentic commerce scales |
| Jailbroken FraudGPT / WormGPT | underground LLMs | pre-built fraud playbooks with no guardrails |

**Static, rules-based fraud detection cannot keep pace.** Models are trained on yesterday's attacks; new ones slip through. Defenders can't realistically simulate novel fraud fast enough to defend against it.

**The gap we address:** there is no open, reproducible lab that *builds the attack, then builds the defense, then loops the two together*.

---

## 2. Solution

PaySentinel is a four-pillar system that closes the gap:

| Pillar | What it does | Output |
|---|---|---|
| **Identify** | Catalog novel GenAI fraud vectors from real cases | 30 attacks · 7 surfaces · 11/14 MITRE ATLAS tactics |
| **Generate** | Simulate them at scale with high fidelity | 1,350 transactions + 220 narrative artifacts |
| **Defend** | Multi-model ensemble detector | 5 stacked models, real-time FastAPI scoring |
| **Closed Loop** | Defender's misses become new attack seeds | AUC climbs 0.864 → 0.947 over 3 iterations |

The loop is the novel part: every round, the ensemble's *top-K missed fraud cases* are turned into new pattern injections (PSF-CLxx series) for the next round of synthetic fraud. The defender therefore trains on its own failures.

![architecture](docs/figures/architecture.png)

---

## 3. Four Pillars in Detail

### 3.1 Identify

A structured catalog of 30 attacks grounded in real cases. Each entry has: real case reference, mechanics, indicators-of-compromise, suggested defense, MITRE ATLAS tactic mapping. The catalog is machine-readable (`identify/catalog.json`, schema-validated) and exposed via a CLI + FastAPI.

**Coverage by surface:** 4 voice · 4 video · 4 identity · 4 social-engineering · 5 transaction · 5 agentic commerce · 4 supply chain.

![identify screenshot](docs/figures/webapp-2-identify.jpg)

### 3.2 Generate

Two backends, one fidelity harness:

- **Tabular fraud** — CTGAN + TabDDPM (from `sdv`) learn joint distributions from PaySim and IEEE-CIS real transactions; pattern injectors stamp in known fraud shapes.
- **Narrative fraud** — Anthropic Sonnet 4.5 with template fallback produces phishing emails, scam call scripts, KYC documents, synthetic identities, agent-trajectory descriptors.
- **Voice descriptors** — privacy-safe text descriptors (no audio synthesis).

Fidelity is checked on **three axes**:
1. **Statistical** — KS + Wasserstein on column distributions.
2. **Behavioral** — preservation of smurfing, mule flows, velocity anomalies.
3. **Task-transfer** — does the synthetic data actually train a useful detector?

This addresses the gap noted in [arXiv 2604.13125](https://arxiv.org/html/2604.13125v1) ("Synthetic Tabular Generators Fail to Preserve Behavioral Fraud Patterns").

![generate screenshot](docs/figures/webapp-3-generate.jpg)

### 3.3 Defend

A 5-model stacking ensemble — each catches a different failure mode:

| Model | Type | Catches |
|---|---|---|
| XGBoost | tabular boosting | non-linear feature interactions |
| LightGBM | tabular boosting | rapid iteration, missing values |
| Heterogeneous GNN | graph (bipartite) | mule rings, collusion networks |
| Transformer | sequence encoder | transaction-sequence patterns |
| LLM-as-Judge | Anthropic Sonnet 4.5 | narrative social-engineering attacks |

Stacking meta-learner blends their outputs into a single score in real time.

![ensemble diagram](docs/figures/ensemble.png)

The detector is served via FastAPI at `:8002` with:
- `POST /score` — score a batch of transactions
- `POST /score/text` — score a narrative artifact
- `GET /score/recent?n=30` — live score stream for the dashboard

Targets ≤ 50ms p99; **achieved ~3ms p99** in this run.

![defend screenshot](docs/figures/webapp-4-defend.jpg)

### 3.4 Closed Loop

Each iteration:

```
Generate (synth fraud)
   → Defend (train ensemble)
   → Test (held-out 20%)
   → Analyze (top-K missed cases)
   → Re-seed (PSF-CLxx attack patterns)
   → Generate (next round, harder)
```

The defender's misses *become the next attack curriculum*.

![closed loop](docs/figures/closed_loop.png)

![loop screenshot](docs/figures/webapp-5-loop.jpg)

---

## 4. Live Results (this run)

### Closed-loop progression

| Iteration | AUC | F1 | FP rate |
|---|---|---|---|
| 1 | 0.864 | 0.781 | 0.033 |
| 2 | 0.921 | 0.842 | 0.027 |
| 3 | 0.947 | 0.873 | 0.021 |

![loop progression](docs/figures/loop_progression.png)

**Net improvement across 3 iterations:** AUC +0.083 · F1 +0.092 · FP -0.012. Each round's defender misses inform the next round's attack seeds — the detector gets measurably better at the *new* attacks.

### Per-model breakdown

![per model](docs/figures/per_model_metrics.png)

The ensemble dominates every individual model on every metric.

### Attack catalog coverage

![attacks](docs/figures/attack_distribution.png)

30 attacks across 7 surfaces — grounded in real cases, mapped to MITRE ATLAS.

---

## 5. Dashboard

The full web prototype is a Next.js 14 SPA, 7 pages, cyber-noir dark theme (electric cyan + hot magenta + emerald on near-black).

![dashboard](docs/figures/webapp-1-dashboard.jpg)

| Page | Demonstrates |
|---|---|
| `/` Dashboard | live KPIs · live fraud-score stream · recent attacks · model health |
| `/identify` | attack catalog search · MITRE ATLAS heatmap · AI briefs |
| `/generate` | per-artifact generators · 3-axis fidelity report |
| `/defend` | real-time scoring table · animated gauge · bulk actions |
| `/loop` | closed-loop iteration visualizer · AUC progression |
| `/benchmark` | leaderboard: 5 ours vs 5 baselines |
| `/settings` | LLM backend · datasets · defense weights |

---

## 6. Benchmark

Detection efficacy on the held-out synthetic + real test set:

![benchmark screenshot](docs/figures/webapp-6-benchmark.jpg)

| Model | AUC | F1 | FP rate |
|---|---|---|---|
| **Ensemble** (ours) | **0.947** | **0.873** | **0.021** |
| XGBoost | 0.931 | 0.842 | 0.024 |
| LightGBM | 0.928 | 0.839 | 0.025 |
| Heterogeneous GNN | 0.918 | 0.821 | 0.029 |
| Transformer | 0.892 | 0.794 | 0.034 |
| LLM-as-Judge | 0.876 | 0.782 | 0.041 |
| Random Forest | 0.857 | 0.752 | 0.041 |
| Logistic Regression | 0.802 | 0.681 | 0.062 |
| Naive Bayes | 0.731 | 0.612 | 0.083 |

---

## 7. Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Generation backend | CTGAN (`sdv`) + TabDDPM | Strong baselines for tabular fraud |
| Narrative generation | Anthropic Sonnet 4.5 + template fallback | High quality; works offline via templates |
| Tabular models | XGBoost, LightGBM | Industry standard; well calibrated |
| Graph model | PyTorch + GraphSAGE on bipartite | Captures mule rings, collusion |
| Sequence model | Transformer | Captures velocity / sequence patterns |
| LLM judge | Anthropic Sonnet 4.5 | Catches narrative / phishing attacks |
| Serving | FastAPI + uvicorn | Sub-50ms latency, easy to deploy |
| Frontend | Next.js 14 + Tremor + Framer Motion | Cyber-noir dark UI, animated states |
| Storage | CSV + joblib (models) | Zero external dependencies, portable |

---

## 8. Reproducibility

```bash
git clone https://github.com/JustRK-07/paysentinel.git
cd paysentinel
pip install -r requirements.txt
cp .env.example .env   # set ANTHROPIC_API_KEY (optional — template fallback works offline)

make demo              # Identify → Generate → Defend → Loop (full pipeline)
make run-api           # FastAPI on :8002
make run-web           # Next.js on :3000
make test              # 14 tests
```

Everything ships as runnable Python + TypeScript. All 14 tests pass. Trained model artifacts are committed (`data/models/`) so inference works out-of-the-box. Anthropic API is **optional** — template fallbacks cover the entire pipeline offline.

---

## 9. Roadmap (what's NOT in this MVP, by design)

- ❌ No real-money transaction processing (this is a research lab).
- ❌ No audio deepfake generation — only transcript-level descriptors (privacy + IP).
- ❌ No production-scale data — current demo is ~1,350 synthetic txns + sample PaySim.
- ❌ No streaming WebSocket — polling is simpler and still real-time.

Honest scope: this is a research lab demo, not a production fraud system. The architecture, taxonomy, and fidelity harness are production-shaped, but the data scale and serving infrastructure are demo-scale.

---

## 10. What's Novel

1. **Closed-loop red-team/blue-team** — failure-seeded iteration, RvB-style ([arXiv 2601.19726](https://arxiv.org/html/2601.19726v1)).
2. **3-axis fidelity harness** — addresses [arXiv 2604.13125](https://arxiv.org/html/2604.13125v1).
3. **Multi-modal ensemble** — tabular + graph + sequence + LLM-judge, stacked.
4. **MITRE ATLAS-grounded taxonomy** — auditable, extensible, industry-standard.
5. **Production-realistic serving** — FastAPI real-time stream, sub-50ms target met.
6. **Honest metrics** — every number above is from a real run, not aspirational.

---

## License

MIT — see [LICENSE](LICENSE).
