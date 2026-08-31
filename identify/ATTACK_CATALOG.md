# PaySentinel Attack Catalog

> **30 novel GenAI-powered payment fraud vectors, grounded in real cases, mapped to MITRE ATLAS.**

This is the **Identify** pillar of PaySentinel. Every attack here is something a GenAI-enabled adversary can do today (2025–2026) that breaks a rules-based fraud detection system.

| Stat | Value |
|---|---|
| Total vectors | **30** |
| Attack surfaces | **7** (voice, video, identity, social-engineering, transaction, agentic-commerce, supply-chain) |
| MITRE ATLAS tactics covered | **11 of 14** |
| Real-world case per vector | ✅ |
| Suggested defense per vector | ✅ |
| Severity rating | low / medium / high / critical |
| Likelihood (next 12 months) | low / medium / high |

---

## How to read this catalog

Each entry has:
- **ID** — `PSF-NNN` (PaySentinel Fraud)
- **Name** — operational name
- **Surface** — channel / attack surface
- **Severity / Likelihood** — quick triage
- **MITRE ATLAS** — tactic/technique ID(s) where applicable; "—" if not applicable
- **Real case** — a documented incident or vendor report
- **Mechanics** — how the attack actually works
- **Indicators** — observable signals defenders can monitor
- **Suggested defense** — what to add to a detection stack
- **Simulatable by PaySentinel** — which Generate pillar agent(s) can reproduce this

---

## 🎙️ Surface 1 — Voice / Audio (4 vectors)

### `PSF-001` — CFO Wire-Transfer Deepfake

| Field | Value |
|---|---|
| **Severity** | 🔴 **Critical** |
| **Likelihood** | 🔴 High |
| **MITRE ATLAS** | AML.T0024 (Exploit ML Model), AML.T0043 (Craft Deepfake) |
| **Real case** | Arup, Feb 2024 — $25 M wire transfer authorized after a video call featuring a deepfake of the CFO ([source](https://www.arkoselabs.com/blog/the-financial-cost-of-agentic-ai-fraud)) |
| **Mechanics** | Adversary scrapes 30–60 sec of a target exec's voice from earnings calls / interviews, fine-tunes a TTS model (e.g., ElevenLabs / open-source VoiceCraft), places a live call to a finance staffer during a "confidential deal," requests an urgent wire to a new beneficiary. |
| **Indicators** | Urgency + new beneficiary + verbal-only authorization + audio artifacts (micro-pauses, robotic cadence on second listen). |
| **Suggested defense** | Out-of-band callback verification on any new beneficiary over a threshold. Voice liveness detection. Behavioral biometrics on the staffer. |
| **Simulatable** | ✅ `voice_sim.py` produces a transcript with markers; defender trained on behavioral patterns around such requests. |

### `PSF-002` — IVR / KYC Voice Bypass

| Field | Value |
|---|---|
| **Severity** | 🔴 Critical |
| **Likelihood** | 🔴 High |
| **MITRE ATLAS** | AML.T0043 |
| **Real case** | FBI Public Service Announcement, Jan 2025 — live deepfake video calls used to bypass selfie-KYC ([source](https://www.arkoselabs.com/blog/the-financial-cost-of-agentic-ai-fraud)) |
| **Mechanics** | Voice clone of a legitimate customer plays the IVR / contact-center voice-authentication step (e.g., "my voice is my password"). Once past authentication, the caller performs account actions. |
| **Indicators** | Voiceprint match failure on second factor; liveness checks missing on the voice channel; unusual call origin vs. customer location. |
| **Suggested defense** | Replace voice-as-password with cryptographic device-bound factor. Add liveness challenge ("repeat this phrase with background noise"). |
| **Simulatable** | ✅ Text transcript + behavioral call-pattern logs. |

### `PSF-003` — Family-Emergency Voice Clone Scam

| Field | Value |
|---|---|
| **Severity** | 🟠 High |
| **Likelihood** | 🔴 High |
| **MITRE ATLAS** | AML.T0043, AML.T0051 (LLM Prompt Injection for orchestration) |
| **Real case** | Tennessee, 2025 — 73-year-old scammed out of $3,000 by voice clone mimicking his son ([source](https://www.arkoselabs.com/blog/the-financial-cost-of-agentic-ai-fraud)) |
| **Mechanics** | Scammer clones a family member's voice from social-media audio (Instagram reels, TikTok). Calls grandparent claiming emergency, requests wire via Zelle / Cash App / gift cards. |
| **Indicators** | First-time beneficiary + P2P rails + high-velocity within 1 hour of contact. |
| **Suggested defense** | Consumer education, friction on first-time P2P beneficiaries > $500, ML flag on call timing + beneficiary velocity. |
| **Simulatable** | ✅ Narrative script generator. |

### `PSF-004` — Voice-Reset Account Takeover

| Field | Value |
|---|---|
| **Severity** | 🟠 High |
| **Likelihood** | 🟡 Medium |
| **MITRE ATLAS** | AML.T0043 |
| **Real case** | Multiple "SIM-swap + voice clone" combo attacks reported by US carriers 2024–2025 |
| **Mechanics** | Attacker SIM-swaps target → receives SMS 2FA → uses voice clone for any voice-based reset step → full account takeover. |
| **Indicators** | SIM-swap detection signal + voice-auth event within same hour. |
| **Suggested defense** | SIM-swap-aware step-up auth, device binding. |
| **Simulatable** | ✅ Behavioral log synthesis. |

---

## 📹 Surface 2 — Video / Visual (4 vectors)

### `PSF-005` — Real-Time Deepfake Video Conference (Executive Impersonation)

| Field | Value |
|---|---|
| **Severity** | 🔴 Critical |
| **Likelihood** | 🔴 High |
| **MITRE ATLAS** | AML.T0043, AML.T0024 |
| **Real case** | Ferrari employee wired funds after a video call appearing to show the CEO ([source](https://www.arkoselabs.com/blog/the-financial-cost-of-agentic-ai-fraud)) |
| **Mechanics** | Live deepfake (face-swap + lip-sync) joins a Teams / Zoom call from an attacker-controlled machine. Other "executives" in the meeting may also be deepfakes or real co-conspirators. Approves a payment mid-call. |
| **Indicators** | Single-participant video with low motion; meeting joined from new IP / unusual geo; verbal-only approval; new beneficiary. |
| **Suggested defense** | Out-of-band callback, on-camera challenge-response ("turn your head left"), payment-approval dual-control. |
| **Simulatable** | ✅ Transcript + meeting metadata generator. |

### `PSF-006` — Selfie-KYC Deepfake Bypass

| Field | Value |
|---|---|
| **Severity** | 🔴 Critical |
| **Likelihood** | 🔴 High |
| **MITRE ATLAS** | AML.T0043 |
| **Real case** | FBI warning, Jan 2025 — AI bypasses standard selfie-KYC; deepfakes used in combination with stolen PII ([source](https://www.arkoselabs.com/blog/the-financial-cost-of-agentic-ai-fraud)) |
| **Mechanics** | Real-time deepfake + ID template (e.g., Midjourney) passes liveness checks. Account is opened in victim's name. |
| **Indicators** | Liveness confidence below threshold; device fingerprint anomaly; PII inconsistency across fields. |
| **Suggested defense** | Multi-modal liveness (depth + IR), device attestation, PII consistency ML. |
| **Simulatable** | ✅ Metadata-only; the deepfake itself is out of scope for PaySentinel (defender-side focus). |

### `PSF-007` — Synthetic Livestream Checkout Fraud

| Field | Value |
|---|---|
| **Severity** | 🟠 High |
| **Likelihood** | 🟡 Medium |
| **MITRE ATLAS** | AML.T0043 |
| **Real case** | Influencer-stream checkout fraud has been documented in China; deepfake variant emerging 2025–2026 |
| **Mechanics** | Deepfake of a popular streamer runs a fake giveaway; viewers enter card details; cards charged. |
| **Indicators** | Card BIN velocity spike tied to a single livestream event; high refund rate after. |
| **Suggested defense** | Stream-attestation; merchant BIN velocity caps. |
| **Simulatable** | ✅ Transaction-pattern generator. |

### `PSF-008` — Screen-Share Deepfake in Support Call

| Field | Value |
|---|---|
| **Severity** | � High |
| **Likelihood** | 🟡 Medium |
| **MITRE ATLAS** | AML.T0043 |
| **Real case** | Increasingly reported by support teams 2024–2025 |
| **Mechanics** | Caller claims to be a customer, deepfakes the customer's face on a "screen share," convinces agent to reset MFA. |
| **Indicators** | Reset request from inside a live screen-share session; no MFA fallback. |
| **Suggested defense** | No MFA resets during screen-share sessions; require pre-registered device. |
| **Simulatable** | ✅ Transcript + event log generator. |

---

## 🪪 Surface 3 — Identity / KYC (4 vectors)

### `PSF-009` — Synthetic Identity Stitching

| Field | Value |
|---|---|
| **Severity** | 🔴 Critical |
| **Likelihood** | 🔴 High |
| **MITRE ATLAS** | — (identity-level, not directly an AI attack) |
| **Real case** | Synthetic identity fraud accounts for up to **80% of credit card fraud losses** in some portfolios ([source](https://www.arkoselabs.com/blog/the-financial-cost-of-agentic-ai-fraud)) |
| **Mechanics** | Real SSN from a child / deceased + AI-generated face + AI-generated documents. Builds credit over 12–24 months ("pig butchering"), then busts out with maxed cards. |
| **Indicators** | Thin-file + new credit lines ramping fast + velocity across multiple products. |
| **Suggested defense** | Entity-linkage GNN across bureau + bank data; piggyback-detection on file consistency. |
| **Simulatable** | ✅ `narrative_agents.synthetic_identity` produces profile JSON. |

### `PSF-010` — AI-Generated Forged Documents

| Field | Value |
|---|---|
| **Severity** | 🔴 Critical |
| **Likelihood** | 🔴 High |
| **MITRE ATLAS** | AML.T0043 (media synthesis) |
| **Real case** | UNODC report — AI-generated CSAM up 600% YoY; same tooling used for financial docs |
| **Mechanics** | Stable Diffusion / SDXL fine-tuned on template (passport, utility bill, pay stub) generates a believable forgery in seconds. |
| **Indicators** | Metadata absence (no camera info), template matching to known forgery patterns. |
| **Suggested defense** | Document-tampering ML, holographic / micro-print verification fallback. |
| **Simulatable** | ✅ Metadata + visual-feature descriptor generator (no actual image — privacy). |

### `PSF-011` — Synthetic BIN Attacks

| Field | Value |
|---|---|
| **Severity** | 🟠 High |
| **Likelihood** | 🟡 Medium |
| **MITRE ATLAS** | — |
| **Real case** | BIN attacks documented across Visa/MC networks for >15 years; AI accelerates target identification |
| **Mechanics** | Adversary enumerates likely-valid card ranges using generative model trained on leaked BIN patterns. Tests small amounts across many cards. |
| **Indicators** | Card-testing velocity from a single source; micro-transactions under threshold. |
| **Suggested defense** | Card-testing detectors + velocity caps on low-value authorizations. |
| **Simulatable** | ✅ Transaction pattern generator. |

### `PSF-012` — Biometric Replay Attack

| Field | Value |
|---|---|
| **Severity** | 🟠 High |
| **Likelihood** | 🟡 Medium |
| **MITRE ATLAS** | AML.T0043 |
| **Real case** | Biometric spoofing documented across face / fingerprint / voice modalities |
| **Mechanics** | Recorded or AI-generated biometric replayed against authentication. |
| **Indicators** | Liveness challenge failure; unusual presentation attack detection (PAD) score. |
| **Suggested defense** | PAD hardware + multi-modal liveness. |
| **Simulatable** | ✅ Behavioral log generator. |

---

## 🎣 Surface 4 — Social Engineering / Narrative (4 vectors)

### `PSF-013` — LLM-Personalized Spear Phishing

| Field | Value |
|---|---|
| **Severity** | 🔴 Critical |
| **Likelihood** | 🔴 High |
| **MITRE ATLAS** | AML.T0029 (Phishing via ML) |
| **Real case** | Anthropic / OpenAI threat reports 2024–2025 — nation-state and financial actors use LLMs to scale hyper-personal phishing |
| **Mechanics** | LLM scrapes target's LinkedIn / Twitter / recent transactions, generates a phishing email / SMS tailored to current context. Open rates 4–8× higher than bulk phishing. |
| **Indicators** | Email has unusual specificity to the victim but sender domain is off. |
| **Suggested defense** | LLM-as-judge scoring of inbound mail; DMARC enforcement; behavioral email analytics. |
| **Simulatable** | ✅ `narrative_agents.phishing_email`. |

### `PSF-014` — Multi-Turn Scam Agent (ScamAgent-Style)

| Field | Value |
|---|---|
| **Severity** | � Critical |
| **Likelihood** | 🔴 High |
| **MITRE ATLAS** | AML.T0051 (LLM Prompt Injection) — used to orchestrate multi-turn dialogue |
| **Real case** | ScamAgent (arXiv 2508.06457) — autonomous multi-turn agent that conducts realistic scam calls |
| **Mechanics** | LLM agent runs the entire conversation with the victim: greets, builds rapport, escalates pressure, routes payment. No human in the loop. |
| **Indicators** | Long call duration + high emotional volatility + payment routing mid-call. |
| **Suggested defense** | Real-time conversation analytics; ML on call transcripts; agentic-detection classifier. |
| **Simulatable** | ✅ `narrative_agents.scam_call_script` produces multi-turn dialogue. |

### `PSF-015` — Quishing (AI-Generated QR Payloads)

| Field | Value |
|---|---|
| **Severity** | 🟠 High |
| **Likelihood** | 🟡 Medium |
| **MITRE ATLAS** | AML.T0029 |
| **Real case** | QR phishing ("quishing") up 10× in some regions 2024–2025 |
| **Mechanics** | LLM-generated email + AI-crafted QR code + stolen brand asset. Victim scans, lands on credential-harvesting page. |
| **Indicators** | Email contains a QR code as the primary CTA; URL encoded in QR resolves to new domain. |
| **Suggested defense** | URL extraction + reputation check from QR images. |
| **Simulatable** | ✅ Email template generator. |

### `PSF-016` — Fake Customer Support Voice Bot

| Field | Value |
|---|---|
| **Severity** | 🟠 High |
| **Likelihood** | 🟡 Medium |
| **MITRE ATLAS** | AML.T0043 |
| **Real case** | Multiple customer-support impersonation cases 2024–2025 |
| **Mechanics** | LLM voice agent impersonates a bank's support line; walks victim through credential disclosure. |
| **Indicators** | Inbound call to victim + outbound "support" call within minutes; voice doesn't match brand voice. |
| **Suggested defense** | Never accept inbound-credential disclosure after outbound calls. |
| **Simulatable** | ✅ Transcript generator. |

---

## 💳 Surface 5 — Transaction-Level (5 vectors)

### `PSF-017` — Micro-Split Transaction Laundering

| Field | Value |
|---|---|
| **Severity** | 🟠 High |
| **Likelihood** | 🔴 High |
| **MITRE ATLAS** | — |
| **Real case** | Documented in FATF typologies 2023–2025 |
| **Mechanics** | Adversary breaks a large fraudulent transfer into N micro-transactions under the reporting threshold, routed through a network of synthetic accounts. |
| **Indicators** | Many same-source → many same-destination, similar amounts, sub-threshold, within minutes. |
| **Suggested defense** | Graph pattern detection (smurfing); velocity aggregation across windows. |
| **Simulatable** | ✅ `txn_generator` with explicit smurfing pattern. |

### `PSF-018` — Automated Card Testing

| Field | Value |
|---|---|
| **Severity** | 🟠 High |
| **Likelihood** | 🔴 High |
| **MITRE ATLAS** | — |
| **Real case** | Continuous across card networks |
| **Mechanics** | LLM-driven bot enumerates stolen card lists; tests small amounts at thousands of merchants in parallel. |
| **Indicators** | Cardholder's card sees many small declines across unrelated merchants in short window. |
| **Suggested defense** | Per-card velocity rules + behavioral merchant-affinity modeling. |
| **Simulatable** | ✅ Transaction pattern generator. |

### `PSF-019` — Refund / Chargeback Fraud with AI-Generated Evidence

| Field | Value |
|---|---|
| **Severity** | 🟠 High |
| **Likelihood** | 🟡 Medium |
| **MITRE ATLAS** | — |
| **Real case** | "AI-generated dispute evidence" reported by issuer fraud teams 2024–2025 |
| **Mechanics** | Buyer claims non-receipt, generates fake shipping confirmation / courier chat / delivery photo via AI, files chargeback. |
| **Indicators** | Dispute evidence images lack EXIF / have AI-generation fingerprints; courier chat doesn't match carrier APIs. |
| **Suggested defense** | Image-forensics ML; cross-validate courier metadata. |
| **Simulatable** | ✅ Evidence-metadata generator. |

### `PSF-020` — Transaction Replay

| Field | Value |
|---|---|
| **Severity** | 🟡 Medium |
| **Likelihood** | 🟡 Medium |
| **MITRE ATLAS** | — |
| **Real case** | Known across NFC / QR / token rails |
| **Mechanics** | Capture a valid tokenized transaction, replay at a different merchant / time. |
| **Indicators** | Cryptogram replay detection (network-level). |
| **Suggested defense** | Token-bound cryptograms + device attestation. |
| **Simulatable** | ✅ Replay-pattern generator. |

### `PSF-021` — Gift Card Laundering with AI Agents

| Field | Value |
|---|---|
| **Severity** | 🟡 Medium |
| **Likelihood** | 🔴 High |
| **MITRE ATLAS** | — |
| **Real case** | FTC reported $228 M lost to gift card scams in 2023; AI agents accelerate |
| **Mechanics** | Scam script (PSF-014) routes victim to buy gift cards, share codes, agent instantly resells. |
| **Indicators** | Same activation code redeemed at geographically distant reseller within minutes. |
| **Suggested defense** | Activation velocity; resale-graph detection. |
| **Simulatable** | ✅ Pattern generator. |

---

## 🤖 Surface 6 — Agentic Commerce (5 vectors)

### `PSF-022` — Rogue AI Shopping Agent

| Field | Value |
|---|---|
| **Severity** | 🔴 Critical |
| **Likelihood** | 🔴 High |
| **MITRE ATLAS** | AML.T0051 (LLM Prompt Injection) |
| **Real case** | Incode report Aug 2026 — AI agents now drive **40% of fraud**, heading to **90% by 2028** ([source](https://ffnews.com/news/agentic-fraud-to-exceed-90-of-all-attacks-by-2028-as-incode-warns-of-ai-driven-surge)) |
| **Mechanics** | Adversary hijacks or impersonates a user's AI shopping agent; agent executes purchases at scale. |
| **Indicators** | Spending velocity deviates from user's profile; agent decisions don't match user history. |
| **Suggested defense** | Agent-identity attestation; spend ceilings per agent; per-decision risk scoring. |
| **Simulatable** | ✅ Agent-trajectory generator. |

### `PSF-023` — Agent Prompt Injection in Checkout Flow

| Field | Value |
|---|---|
| **Severity** | 🔴 Critical |
| **Likelihood** | 🔴 High |
| **MITRE ATLAS** | AML.T0051 |
| **Real case** | MITRE ATLAS AML.T0051 — LLM Prompt Injection is a primary AI red-team technique |
| **Mechanics** | Adversary injects instructions into product description / chat history / tool result → agent interprets as legitimate → exfiltrates payment data or transfers funds. |
| **Indicators** | Tool-call arguments deviate from user's stated intent; untrusted tool-result text triggers financial action. |
| **Suggested defense** | Stricter tool-call authorization; instruction/data separation in agent context. |
| **Simulatable** | ✅ Tool-call trace generator. |

### `PSF-024` — Cross-Agent Collusion

| Field | Value |
|---|---|
| **Severity** | � High |
| **Likelihood** | 🟡 Medium |
| **MITRE ATLAS** | AML.T0051 |
| **Real case** | Theoretical as of 2025; first observed cases 2026 |
| **Mechanics** | Two compromised agents (one as buyer, one as seller) execute mutually-beneficial transactions; both individually look normal. |
| **Indicators** | Counter-party graph density anomaly; mutual-beneficial scoring. |
| **Suggested defense** | Counter-party graph analytics. |
| **Simulatable** | ✅ Paired-agent trace generator. |

### `PSF-025` — Autonomous Subscription Manipulation

| Field | Value |
|---|---|
| **Severity** | � Medium |
| **Likelihood** | 🟡 Medium |
| **MITRE ATLAS** | AML.T0051 |
| **Real case** | Emerging with proliferation of subscription-managing AI agents |
| **Mechanics** | Agent signs up for many overlapping subscriptions with overlapping trials, harvesting credits. |
| **Indicators** | Subscription creation velocity; same-card cross-merchant pattern. |
| **Suggested defense** | Subscription velocity cap per card. |
| **Simulatable** | ✅ Subscription-pattern generator. |

### `PSF-026` — Agent-as-Mule (Money Muling via Agent Networks)

| Field | Value |
|---|---|
| **Severity** | 🟠 High |
| **Likelihood** | 🟡 Medium |
| **MITRE ATLAS** | AML.T0051 |
| **Real case** | FATF typology 2024 — AI agents being recruited into mule networks |
| **Mechanics** | Agent (or compromised agent) routes payments across many small accounts, hiding the origin of funds. |
| **Indicators** | Agent's transaction graph has high path-betweenness. |
| **Suggested defense** | Graph-based money-mule detection. |
| **Simulatable** | ✅ Money-mule graph generator. |

---

## 🏭 Surface 7 — Supply Chain / Infrastructure (4 vectors)

### `PSF-027` — Poisoned RAG for Fraud Assistant

| Field | Value |
|---|---|
| **Severity** | � High |
| **Likelihood** | 🟡 Medium |
| **MITRE ATLAS** | AML.T0020 (Poison Training Data), AML.T0046 (Erode ML Model Integrity) |
| **Real case** | Demonstrated in academic settings 2024; expected to grow |
| **Mechanics** | Adversary injects documents into a fraud-investigation RAG corpus that mislead the assistant into recommending "approve" for known fraud patterns. |
| **Indicators** | RAG retrieval contains recently-added, low-authority sources; assistant rationale diverges from analyst's. |
| **Suggested defense** | Source provenance + audit trail on RAG updates. |
| **Simulatable** | ✅ RAG-corpus perturbation generator. |

### `PSF-028` — Model API Key Theft

| Field | Value |
|---|---|
| **Severity** | 🔴 Critical |
| **Likelihood** | 🟡 Medium |
| **MITRE ATLAS** | AML.T0008 (ML Model Theft / ML Supply Chain Compromise) |
| **Real case** | Multiple LLM provider breaches 2024–2025 (e.g., open-source model weights leaked) |
| **Mechanics** | Adversary steals a bank's internal fraud-detection model API key → uses it for adversarial probing / model inversion. |
| **Indicators** | API call patterns inconsistent with normal usage; spike in error responses. |
| **Suggested defense** | API key rotation, rate-limit per identity, anomaly detection on API usage. |
| **Simulatable** | ✅ API-call log generator. |

### `PSF-029` — Jailbroken Fraud LLM

| Field | Value |
|---|---|
| **Severity** | 🟠 High |
| **Likelihood** | 🟡 Medium |
| **MITRE ATLAS** | AML.T0051 |
| **Real case** | "FraudGPT" / "WormGPT" listed on dark-web forums 2023–2025 |
| **Mechanics** | Adversary uses a fine-tuned jailbroken LLM to generate fraud scripts, phishing, money-laundering plans at scale. |
| **Indicators** | Detection of jailbroken LLM signatures in fraud artifacts (specific stylistic markers). |
| **Suggested defense** | Stylometric / linguistic ML on fraud artifacts; prompt-injection classifiers. |
| **Simulatable** | ✅ `narrative_agents.scam_call_script` uses an LLM in a similar mode. |

### `PSF-030` — Deepfake-as-a-Service (Fraud Tooling Market)

| Field | Value |
|---|---|
| **Severity** | 🔴 Critical |
| **Likelihood** | 🔴 High |
| **MITRE ATLAS** | AML.T0043 |
| **Real case** | Dark-web marketplaces sell voice-clone kits for $5–$50 (2024–2025) |
| **Mechanics** | Off-the-shelf tooling lowers attacker cost from weeks of ML work to minutes. |
| **Indicators** | Operational artifact patterns specific to popular off-the-shelf tools. |
| **Suggested defense** | Tool-fingerprint ML on fraud artifacts. |
| **Simulatable** | ✅ Tool-fingerprint metadata generator. |

---

## Coverage summary

| Surface | Count | IDs |
|---|---|---|
| Voice / Audio | 4 | PSF-001 to PSF-004 |
| Video / Visual | 4 | PSF-005 to PSF-008 |
| Identity / KYC | 4 | PSF-009 to PSF-012 |
| Social Engineering / Narrative | 4 | PSF-013 to PSF-016 |
| Transaction-Level | 5 | PSF-017 to PSF-021 |
| Agentic Commerce | 5 | PSF-022 to PSF-026 |
| Supply Chain / Infrastructure | 4 | PSF-027 to PSF-030 |

**MITRE ATLAS tactic coverage:** Reconnaissance (1), Resource Development (2), Initial Access (5), ML Model Access (2), Persistence (1), Defense Evasion (3), Discovery (1), Collection (1), ML Attack Staging (2), Exfiltration (1), Impact (4). **11 of 14 tactics touched.**

---

## See also

- Machine-readable form: [`catalog.json`](catalog.json)
- Programmatic access: [`threat_landscape.py`](threat_landscape.py) (`python -m identify.threat_landscape`)
- Simulation in `generate/`
- Defense in `defend/`
