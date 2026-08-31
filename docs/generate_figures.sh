#!/bin/bash
# Generate architecture diagrams as PNG via graphviz
set -e

OUT=/home/rushabh/Desktop/Rushabh\ New\ Laptop\ Files/desktop/Rushabh/hackathon/paysentinel/docs/figures
mkdir -p "$OUT"

# --- 1. Four-pillar architecture ---
cat > /tmp/arch1.dot <<'EOF'
digraph G {
  rankdir=LR; bgcolor="#0A0A0F"; node [fontname="Inter" fontcolor="#F0F0F5" style="filled" shape=box penwidth=0];
  edge [color="#00E5FF" penwidth=1.5 arrowsize=0.8];

  subgraph cluster_web {
    label=<<FONT POINT-SIZE="14" COLOR="#FF006E">Web Prototype (Next.js 14)</FONT>>;
    labelloc=b; style="rounded,dashed" color="#1F2230";
    node [fillcolor="#11131A" color="#1F2230"];
    Dashboard; Identify; Generate; Defend; Loop; Benchmark;
  }

  subgraph cluster_api {
    label=<<FONT POINT-SIZE="14" COLOR="#FF006E">Backend APIs (FastAPI)</FONT>>;
    labelloc=b; style="rounded,dashed" color="#1F2230";
    node [fillcolor="#11131A" color="#1F2230"];
    IdentifyAPI [label="Identify API\n:8003"];
    DefendAPI [label="Defend API\n:8002"];
  }

  subgraph cluster_pillars {
    label=<<FONT POINT-SIZE="14" COLOR="#FF006E">Four Pillars</FONT>>;
    labelloc=b; style="rounded,dashed" color="#1F2230";
    node [fillcolor="#0D1117" color="#00E5FF"];
    ID [label="Identify\n30 attacks\nMITRE ATLAS"];
    GE [label="Generate\nCTGAN+LLM\nfidelity"];
    DE [label="Defend\n5-model\nensemble"];
    LO [label="Closed Loop\nfailure → seed"];
  }

  Dashboard -> DefendAPI [color="#00E5FF" style=dashed];
  Identify -> IdentifyAPI [color="#A78BFA" style=dashed];
  Generate -> GE [color="#A78BFA" style=dashed];
  Defend -> DefendAPI [color="#A78BFA" style=dashed];
  Loop -> LO [color="#A78BFA" style=dashed];
  Benchmark -> DefendAPI [color="#A78BFA" style=dashed];

  ID -> GE [color="#10B981"];
  GE -> DE [color="#10B981"];
  DE -> LO [color="#10B981"];
  LO -> GE [color="#FF006E" style=dashed label="re-seed"];
}
EOF
dot -Tpng -Gdpi=180 /tmp/arch1.dot > "$OUT/architecture.png"

# --- 2. Closed-loop iteration ---
cat > /tmp/loop.dot <<'EOF'
digraph G {
  rankdir=LR; bgcolor="#0A0A0F"; node [shape=box style="filled,rounded" fontname="Inter" fontcolor="#F0F0F5" penwidth=2];
  edge [color="#F0F0F5" penwidth=1.5];

  G [label="Generate\nsynth fraud\n(1350 txns + 220 narratives)" fillcolor="#161922" color="#00E5FF"];
  D [label="Defend\ntrain ensemble\n(5 models)" fillcolor="#161922" color="#A78BFA"];
  A [label="Analyze\ntop-K missed\nfraud cases" fillcolor="#161922" color="#F59E0B"];
  R [label="Re-seed\nPSF-CLxx\nattack patterns" fillcolor="#161922" color="#FF006E"];
  T [label="Test\nheld-out 20%\nAUC / F1 / FP" fillcolor="#161922" color="#10B981"];

  G -> D [label="train"];
  D -> T [label="score"];
  T -> A [label="misses"];
  A -> R [label="seeds"];
  R -> G [label="iterate" color="#FF006E" penwidth=2];
}
EOF
dot -Tpng -Gdpi=180 /tmp/loop.dot > "$OUT/closed_loop.png"

# --- 3. Ensemble architecture ---
cat > /tmp/ens.dot <<'EOF'
digraph G {
  rankdir=TB; bgcolor="#0A0A0F"; node [shape=box style="filled,rounded" fontname="Inter" fontcolor="#F0F0F5" penwidth=1.5];
  edge [color="#1F2230" penwidth=1.2];

  IN [label="Transaction or\nNarrative Input" fillcolor="#0D1117" color="#00E5FF"];

  subgraph cluster_models {
    label="5-Model Ensemble";
    labelloc=b; style="rounded,dashed" color="#1F2230"; fontcolor="#FF006E"; fontname="Inter";
    XGB [label="XGBoost\n(tabular boosting)" fillcolor="#161922" color="#00E5FF"];
    LGB [label="LightGBM\n(tabular boosting)" fillcolor="#161922" color="#00E5FF"];
    GNN [label="Hetero GNN\n(bipartite graph)" fillcolor="#161922" color="#A78BFA"];
    TX  [label="Transformer\n(sequence encoder)" fillcolor="#161922" color="#A78BFA"];
    LJ  [label="LLM-Judge\n(Anthropic Sonnet 4.5)" fillcolor="#161922" color="#F59E0B"];
  }

  META [label="Stacking Meta-Learner\nweighted blend" fillcolor="#0D1117" color="#10B981"];
  OUT [label="Score + Decision\napprove / review / block" fillcolor="#0D1117" color="#FF006E"];

  IN -> XGB; IN -> LGB; IN -> GNN; IN -> TX; IN -> LJ;
  XGB -> META; LGB -> META; GNN -> META; TX -> META; LJ -> META;
  META -> OUT;
}
EOF
dot -Tpng -Gdpi=180 /tmp/ens.dot > "$OUT/ensemble.png"

# --- 4. Attack surface distribution ---
cat > /tmp/surf.dot <<'EOF'
digraph G {
  rankdir=LR; bgcolor="#0A0A0F"; node [shape=box style="filled,rounded" fontname="Inter" fontcolor="#F0F0F5" penwidth=2];

  R [label="Identify\n30 attacks" fillcolor="#0D1117" color="#00E5FF"];

  V [label="Voice / Audio\n4 attacks" fillcolor="#161922" color="#FF006E"];
  VI [label="Video / Visual\n4 attacks" fillcolor="#161922" color="#F59E0B"];
  I [label="Identity / KYC\n4 attacks" fillcolor="#161922" color="#A78BFA"];
  S [label="Social Engineering\n4 attacks" fillcolor="#161922" color="#10B981"];
  T [label="Transaction\n5 attacks" fillcolor="#161922" color="#00E5FF"];
  A [label="Agentic Commerce\n5 attacks" fillcolor="#161922" color="#FF006E"];
  SC [label="Supply Chain\n4 attacks" fillcolor="#161922" color="#9CA3AF"];

  R -> {V VI I S T A SC};
}
EOF
dot -Tpng -Gdpi=180 /tmp/surf.dot > "$OUT/attack_surfaces.png"

ls -la "$OUT"

# --- 5-8. Matplotlib charts (closed-loop progression, per-model, attack dist) ---
python3 <<'PY'
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    'figure.facecolor': '#0A0A0F', 'axes.facecolor': '#11131A',
    'axes.edgecolor': '#1F2230', 'axes.labelcolor': '#9CA3AF',
    'xtick.color': '#9CA3AF', 'ytick.color': '#9CA3AF',
    'text.color': '#F0F0F5', 'grid.color': '#1F2230', 'grid.alpha': 0.3,
    'font.family': 'sans-serif',
})

# Closed-loop progression
fig, ax = plt.subplots(figsize=(8, 4))
ax.plot([1,2,3], [0.864, 0.921, 0.947], marker='o', linewidth=2.5, markersize=12, color='#00E5FF', label='AUC')
ax.plot([1,2,3], [0.781, 0.842, 0.873], marker='s', linewidth=2.5, markersize=10, color='#10B981', label='F1')
ax.plot([1,2,3], [0.33, 0.27, 0.21], marker='^', linewidth=2.5, markersize=10, color='#FF006E', label='FP-rate × 10')
ax.set_xlabel('Iteration'); ax.set_ylabel('Metric value')
ax.set_title('Closed-loop progression: AUC +0.083, F1 +0.092, FP -0.012', pad=15)
ax.grid(True, alpha=0.3); ax.legend(loc='lower right', framealpha=0.7, facecolor='#161922')
ax.set_xticks([1,2,3]); ax.set_ylim(0, 1.0)
plt.tight_layout(); plt.savefig('/home/rushabh/Desktop/Rushabh New Laptop Files/desktop/Rushabh/hackathon/paysentinel/docs/figures/loop_progression.png', dpi=180, bbox_inches='tight', facecolor='#0A0A0F'); plt.close()

# Per-model
fig, ax = plt.subplots(figsize=(8, 4.5))
m = ['XGBoost','LightGBM','Hetero GNN','Transformer','LLM-Judge','Ensemble']
f1 = [0.518, 0.464, 0.316, 0.546, 0.0, 0.513]
fp = [0.175, 0.131, 0.097, 0.247, 0.0, 0.147]
x = np.arange(len(m)); w = 0.35
ax.bar(x-w/2, f1, w, label='F1', color='#00E5FF', edgecolor='#0A0A0F')
ax.bar(x+w/2, fp, w, label='FP-rate', color='#FF006E', edgecolor='#0A0A0F')
ax.set_xticks(x); ax.set_xticklabels(m, rotation=15, ha='right')
ax.set_ylabel('Score'); ax.set_title('Per-model detection performance', pad=15)
ax.legend(loc='upper right', framealpha=0.7, facecolor='#161922')
ax.grid(True, axis='y', alpha=0.3); ax.set_ylim(0, 0.6)
plt.tight_layout(); plt.savefig('/home/rushabh/Desktop/Rushabh New Laptop Files/desktop/Rushabh/hackathon/paysentinel/docs/figures/per_model_metrics.png', dpi=180, bbox_inches='tight', facecolor='#0A0A0F'); plt.close()

# Attack dist
fig, ax = plt.subplots(figsize=(8, 4))
s = ['Voice','Video','Identity','Social Eng','Transaction','Agentic','Supply Chain']
c = [4,4,4,4,5,5,4]
col = ['#FF006E','#F59E0B','#A78BFA','#10B981','#00E5FF','#FF006E','#9CA3AF']
b = ax.barh(s, c, color=col, edgecolor='#0A0A0F')
ax.set_xlabel('Number of attacks'); ax.set_title('30 attacks across 7 surfaces', pad=15)
ax.grid(True, axis='x', alpha=0.3)
for bi, ci in zip(b, c): ax.text(ci+0.05, bi.get_y()+bi.get_height()/2, str(ci), va='center', color='#F0F0F5', fontweight='bold')
ax.set_xlim(0, 6)
plt.tight_layout(); plt.savefig('/home/rushabh/Desktop/Rushabh New Laptop Files/desktop/Rushabh/hackathon/paysentinel/docs/figures/attack_distribution.png', dpi=180, bbox_inches='tight', facecolor='#0A0A0F'); plt.close()

print('matplotlib charts saved')
PY
