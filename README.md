# 🛡️ PaySentinel

**Agentic Red-Team Lab for GenAI-Powered Payment Fraud.**

Identify novel fraud attacks → generate realistic simulations → defend with an ensemble detector — all in one closed feedback loop.

![architecture](docs/figures/architecture.png)

---

## What we do

GenAI is making payment fraud faster, cheaper, and harder to spot:

- **Voice cloning** of CFOs (Arup $25M wire fraud, 2024)
- **Deepfake video calls** impersonating executives (Ferrari CEO)
- **LLM-personalized spear phishing** with social-media context
- **Synthetic identity stitching** (real SSN + AI face = 80% of CC losses)
- **Rogue AI shopping agents** spending on users' behalf

Static rules-based fraud detection can't keep pace. PaySentinel takes the opposite stance: **build the attack, then build the defense, then loop.**

![closed loop](docs/figures/closed_loop.png)

---

## Four pillars · one loop

| Pillar | What | Output |
|---|---|---|
| **Identify** | Catalog novel GenAI fraud vectors | 30 attacks · 7 surfaces · 11/14 MITRE ATLAS tactics |
| **Generate** | Simulate them at scale with high fidelity | 1,350 transactions + 220 narrative artifacts |
| **Defend** | Multi-model ensemble detector | 5 models stacked, real-time FastAPI scoring |
| **Closed Loop** | Defender's misses → new attack seeds | AUC improves 0.864 → 0.947 over 3 iterations |

---

## What's in the box

```
identify/    → 30 fraud vectors + MITRE ATLAS mapping + threat-landscape API
generate/    → CTGAN/TabDDPM + LLM agents + 3-axis fidelity harness
defend/      → 5-model stacking ensemble + FastAPI /score /score/text /score/recent
closed_loop/ → failure → seed → retrain pipeline
webapp/      → Next.js 14 prototype, 7 pages, cyber-noir dark theme
docs/        → Solution_Walkthrough.docx + 7 architecture diagrams + writeup script
```

---

## Quick start

```bash
git clone https://github.com/JustRK-07/paysentinel.git
cd paysentinel
pip install -r requirements.txt
make demo              # Identify → Generate → Defend → Loop
make run-api           # FastAPI on :8002
make run-web           # Next.js on :3000
```

All 14 tests pass. Anthropic API is optional — template fallbacks work offline.

---

## License

MIT — see [LICENSE](LICENSE).
