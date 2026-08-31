# Contributing to PaySentinel

Thanks for your interest in extending PaySentinel. Here's how to add a new attack vector, a new generator, or a new detection model.

## Add a new attack vector

1. Append an entry to `identify/catalog.json` following the existing schema.
2. Optionally add a markdown section to `identify/ATTACK_CATALOG.md`.
3. If the attack has a corresponding simulation, add a generator function to `generate/narrative_agents.py` (or `generate/voice_sim.py` for voice artifacts) and register it in the `GENERATORS` dict.

## Add a new generator

1. Implement a function in `generate/narrative_agents.py` that returns a dict with at minimum `type`, `markers`, and the artifact body.
2. Markers are what the Defend pillar trains on. Add at least one structural marker — e.g., urgency, external link, prompt injection, etc.
3. Register the function in `GENERATORS`.
4. Add to `generate/pipeline.py::DEFAULT_NARRATIVE_SPECS` if you want it in the demo.

## Add a new detection model

1. Add a training function to a new `defend/train_<model>.py` (or extend an existing one). The function must return a dict with at least `model_name`, `metrics` (dict of `auc`, `f1`, `precision`, `recall`, `false_positive_rate`, etc.), `n_train`, `n_test`, and `duration_seconds`.
2. Wire it into `defend/train.py::train_all`.
3. Add an entry to `EnsembleConfig.weights` in `defend/ensemble.py`.

## Add a new web page

1. Create `webapp/app/<page>/page.tsx`.
2. Add the route to `components/nav.tsx::NAV`.
3. If you need backend data, add a fetcher to `webapp/lib/api.ts`.

## Style

- Python: PEP 8, ruff (`make lint`).
- TypeScript: ESLint (`cd webapp && npm run lint`).
- Docx: generated from `docs/build_docx.py` — edit the script, regenerate.

## Testing

```bash
make test           # pytest
make lint           # ruff
```
