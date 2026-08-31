import {
  Activity,
  AlertTriangle,
  Cpu,
  Shield,
} from "lucide-react";

export const mockKpis = [
  {
    label: "Attacks identified", value: "30", sub: "across 7 surfaces", icon: AlertTriangle, color: "text-accent",
    delta: "+0", sparkColor: "magenta" as const, sparkKey: "attacks",
    tooltip: "Total distinct GenAI payment fraud vectors catalogued, mapped to MITRE ATLAS tactics.",
    sparkData: Array.from({ length: 12 }, (_, i) => ({ t: i, attacks: 26 + Math.round(Math.random() * 4) })),
  },
  {
    label: "Sims generated", value: "5,840", sub: "txns + 220 narrative", icon: Cpu, color: "text-info",
    delta: "+2,300", sparkColor: "violet" as const, sparkKey: "sims",
    tooltip: "Synthetic fraud artifacts produced by the Generate pillar — both transactions and narrative.",
    sparkData: Array.from({ length: 12 }, (_, i) => ({ t: i, sims: Math.round(2000 + i * 320 + Math.random() * 400) })),
  },
  {
    label: "Live F1", value: "0.873", sub: "blended ensemble", icon: Shield, color: "text-success",
    delta: "+0.083", sparkColor: "emerald" as const, sparkKey: "f1",
    tooltip: "Harmonic mean of precision and recall on the live scoring stream. Higher is better.",
    sparkData: Array.from({ length: 12 }, (_, i) => ({ t: i, f1: parseFloat((0.78 + i * 0.008 + Math.random() * 0.01).toFixed(3)) })),
  },
  {
    label: "FP rate", value: "0.021", sub: "at 50k txns", icon: Activity, color: "text-primary",
    delta: "-0.012", sparkColor: "cyan" as const, sparkKey: "fp",
    tooltip: "False positive rate: legitimate transactions flagged as fraud. Lower is better.",
    sparkData: Array.from({ length: 12 }, (_, i) => ({ t: i, fp: parseFloat((0.033 - i * 0.001 + Math.random() * 0.002).toFixed(4)) })),
  },
];

export const mockScoreStream = Array.from({ length: 60 }, (_, i) => ({
  t: i,
  score: 0.4 + 0.3 * Math.sin(i / 6) + 0.15 * Math.cos(i / 3) + (i > 45 ? 0.1 : 0),
  threshold: 0.5,
}));

export const mockRecentAttacks = [
  { id: "PSF-014", name: "Multi-Turn Scam Agent", severity: "critical" },
  { id: "PSF-022", name: "Rogue AI Shopping Agent", severity: "critical" },
  { id: "PSF-013", name: "LLM Spear Phishing", severity: "critical" },
  { id: "PSF-017", name: "Micro-Split Laundering", severity: "high" },
  { id: "PSF-009", name: "Synthetic Identity Stitching", severity: "critical" },
  { id: "PSF-023", name: "Agent Prompt Injection", severity: "critical" },
];

export const mockCatalog = Array.from({ length: 30 }, (_, i) => {
  const ids = [
    "PSF-001", "PSF-002", "PSF-003", "PSF-004", "PSF-005",
    "PSF-006", "PSF-007", "PSF-008", "PSF-009", "PSF-010",
    "PSF-011", "PSF-012", "PSF-013", "PSF-014", "PSF-015",
    "PSF-016", "PSF-017", "PSF-018", "PSF-019", "PSF-020",
    "PSF-021", "PSF-022", "PSF-023", "PSF-024", "PSF-025",
    "PSF-026", "PSF-027", "PSF-028", "PSF-029", "PSF-030",
  ];
  const surfaces = [
    "voice", "video", "identity", "social_engineering",
    "transaction", "agentic_commerce", "supply_chain",
  ];
  const severities = ["critical", "high", "medium"];
  const likelihoods = ["high", "medium", "low"];
  return {
    id: ids[i],
    name: [
      "CFO Wire-Transfer Deepfake", "IVR / KYC Voice Bypass", "Family-Emergency Voice Clone",
      "Voice-Reset ATO", "Real-Time Deepfake Video Conference", "Selfie-KYC Deepfake Bypass",
      "Synthetic Livestream Checkout Fraud", "Screen-Share Deepfake",
      "Synthetic Identity Stitching", "AI-Generated Forged Documents",
      "Synthetic BIN Attacks", "Biometric Replay Attack", "LLM Spear Phishing",
      "Multi-Turn Scam Agent", "Quishing", "Fake Customer Support Voice Bot",
      "Micro-Split Laundering", "Automated Card Testing", "Refund/Chargeback w/ AI Evidence",
      "Transaction Replay", "Gift Card Laundering", "Rogue AI Shopping Agent",
      "Agent Prompt Injection", "Cross-Agent Collusion", "Autonomous Subscription Manipulation",
      "Agent-as-Mule", "Poisoned RAG", "Model API Key Theft",
      "Jailbroken Fraud LLM", "Deepfake-as-a-Service",
    ][i],
    surface: surfaces[i % surfaces.length],
    severity: severities[i % severities.length],
    likelihood: likelihoods[i % likelihoods.length],
    mechanics: [
      "Adversary scrapes 30-60s of target exec voice from earnings calls, fine-tunes TTS, places live call.",
      "Voice clone passes IVR voice authentication step, then performs account actions.",
      "Clones family member voice from social-media audio, calls grandparent requesting P2P.",
      "SIM-swap target, receive SMS 2FA, use voice clone for reset step, full ATO.",
      "Live deepfake joins Teams/Zoom, approves payment mid-call.",
    ][i % 5],
    indicators: ["urgency", "external_link", "domain_mismatch", "liveness_failure", "velocity_anomaly"],
    suggested_defense: ["out_of_band_callback", "liveness_challenge", "device_binding", "behavioral_ml"],
  };
});

export const mockAtlasHeatmap = {
  AML_T0008: { critical: 1, high: 0, medium: 0, low: 0 },
  AML_T0020: { critical: 0, high: 1, medium: 0, low: 0 },
  AML_T0024: { critical: 2, high: 0, medium: 0, low: 0 },
  AML_T0029: { critical: 1, high: 1, medium: 0, low: 0 },
  AML_T0043: { critical: 6, high: 4, medium: 1, low: 0 },
  AML_T0046: { critical: 0, high: 1, medium: 0, low: 0 },
  AML_T0051: { critical: 4, high: 2, medium: 1, low: 0 },
};

export const mockIterations = [
  {
    iteration: 1,
    blended_auc: 0.864,
    blended_f1: 0.781,
    blended_fp_rate: 0.033,
    n_train: 24000,
    new_seeds: ["PSF-CL01-A:TRANSFER-missed"],
  },
  {
    iteration: 2,
    blended_auc: 0.921,
    blended_f1: 0.842,
    blended_fp_rate: 0.027,
    n_train: 26800,
    new_seeds: ["PSF-CL02-A:TRANSFER-missed", "PSF-CL02-C:high-amount-transfer-evasion"],
  },
  {
    iteration: 3,
    blended_auc: 0.947,
    blended_f1: 0.873,
    blended_fp_rate: 0.021,
    n_train: 28400,
    new_seeds: ["PSF-CL03-C:high-amount-transfer-evasion"],
  },
];

export const mockLiveScoring = Array.from({ length: 30 }, (_, i) => ({
  txn: `T-${(10000 + i).toString()}`,
  amount: Math.round((100 + Math.random() * 50000) * 100) / 100,
  score: Math.random() * (i > 20 ? 0.9 : 0.4) + 0.1,
  decision: ["approve", "approve", "approve", "review", "block"][Math.floor(Math.random() * 5)],
  top_feature: ["drain_flag", "transfer_only_flag", "small_amount_velocity", "external_link"][i % 4],
}));
