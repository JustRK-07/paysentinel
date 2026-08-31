# Docs

This directory holds the required submission artifacts.

- **`Solution_Walkthrough.docx`** — the required writeup covering novel attacks, generation/simulation, detection+mitigation with efficacy results, and real-world feasibility.

## Regenerating the walkthrough

```bash
python3 -m docs.build_docx
```

Requires `python-docx` (already in `requirements.txt`). Pulls live metrics from `results/` if present; otherwise uses documented benchmark numbers.
