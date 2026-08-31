"""
PaySentinel — Identify pillar: Threat Landscape API.

Loads the attack catalog from catalog.json and exposes:
  • CLI summary (rich tables, severity/likelihood distributions)
  • Search + filter
  • FastAPI endpoints for the web prototype
  • Analytics (per-surface stats, ATLAS coverage, severity histogram)

Run:
    python -m identify.threat_landscape              # CLI summary
    python -m identify.threat_landscape --id PSF-014 # one attack detail
    python -m identify.threat_landscape --serve      # FastAPI on :8001
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

CATALOG_PATH = Path(__file__).parent / "catalog.json"

# ----------------------------- catalog loading ----------------------------- #


@dataclass
class Attack:
    """One attack vector from the catalog."""

    id: str
    name: str
    surface: str
    severity: str
    likelihood: str
    mitre_atlas: list[str]
    real_case: dict[str, Any]
    mechanics: str
    indicators: list[str]
    suggested_defense: list[str]
    simulatable_by: list[str]


@dataclass
class Catalog:
    """Top-level catalog with all attacks."""

    version: str
    surfaces: list[str]
    attacks: list[Attack]
    stats: dict[str, Any]


def load_catalog(path: Path = CATALOG_PATH) -> Catalog:
    """Load and validate the attack catalog from disk."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    attacks = [Attack(**a) for a in raw["attacks"]]
    return Catalog(
        version=raw["version"],
        surfaces=raw["surfaces"],
        attacks=attacks,
        stats=raw["stats"],
    )


# ----------------------------- query helpers ----------------------------- #


def filter_attacks(
    catalog: Catalog,
    *,
    surface: str | None = None,
    severity: str | None = None,
    likelihood: str | None = None,
    text: str | None = None,
    atlas: str | None = None,
) -> list[Attack]:
    """Filter attacks by any combination of attributes."""
    out = catalog.attacks
    if surface:
        out = [a for a in out if a.surface == surface]
    if severity:
        out = [a for a in out if a.severity == severity]
    if likelihood:
        out = [a for a in out if a.likelihood == likelihood]
    if atlas:
        out = [a for a in out if atlas in a.mitre_atlas]
    if text:
        q = text.lower()
        out = [
            a
            for a in out
            if q in a.name.lower()
            or q in a.mechanics.lower()
            or any(q in i.lower() for i in a.indicators)
            or any(q in d.lower() for d in a.suggested_defense)
        ]
    return out


def get_attack(catalog: Catalog, attack_id: str) -> Attack | None:
    """Look up one attack by ID, e.g. 'PSF-014'."""
    for a in catalog.attacks:
        if a.id == attack_id:
            return a
    return None


def surface_distribution(catalog: Catalog) -> dict[str, int]:
    """Count attacks per surface."""
    return dict(Counter(a.surface for a in catalog.attacks))


def severity_distribution(catalog: Catalog) -> dict[str, int]:
    """Count attacks per severity level."""
    order = ["critical", "high", "medium", "low"]
    counts = Counter(a.severity for a in catalog.attacks)
    return {k: counts.get(k, 0) for k in order}


def likelihood_distribution(catalog: Catalog) -> dict[str, int]:
    """Count attacks per likelihood level."""
    order = ["high", "medium", "low"]
    counts = Counter(a.likelihood for a in catalog.attacks)
    return {k: counts.get(k, 0) for k in order}


def atlas_coverage(catalog: Catalog) -> dict[str, list[str]]:
    """Map each MITRE ATLAS tactic to the attacks that touch it."""
    out: dict[str, list[str]] = {}
    for a in catalog.attacks:
        for t in a.mitre_atlas:
            out.setdefault(t, []).append(a.id)
    return out


def ai_brief(attack: Attack) -> str:
    """Auto-generated 2-line 'AI brief' for an attack, used by the UI."""
    indicators = ", ".join(attack.indicators[:3])
    defenses = ", ".join(attack.suggested_defense[:2])
    return (
        f"**{attack.severity.upper()}** | {attack.likelihood} likelihood | "
        f"{attack.surface.replace('_', ' ').title()}\n\n"
        f"Watch for: {indicators}. Defend with: {defenses}."
    )


# ----------------------------- CLI ----------------------------- #


def _print_summary(catalog: Catalog) -> None:
    print()
    print(f"  PaySentinel Attack Catalog v{catalog.version}")
    print(f"  {'─' * 60}")
    print(f"  Total attacks:   {len(catalog.attacks)}")
    print(f"  Surfaces:        {len(catalog.surfaces)}")
    print(f"  ATLAS tactics:   {catalog.stats['tactics_covered']} of {catalog.stats['total_tactics']}")
    print()
    print("  By surface:")
    for s, c in surface_distribution(catalog).items():
        print(f"    • {s.replace('_', ' ').title():30s} {c}")
    print()
    print("  By severity:")
    for s, c in severity_distribution(catalog).items():
        print(f"    • {s:10s} {c}")
    print()
    print("  By likelihood:")
    for l, c in likelihood_distribution(catalog).items():
        print(f"    • {l:10s} {c}")
    print()


def _print_attack(attack: Attack) -> None:
    print()
    print(f"  {attack.id} — {attack.name}")
    print(f"  {'─' * 60}")
    print(f"  Surface:     {attack.surface}")
    print(f"  Severity:    {attack.severity}")
    print(f"  Likelihood:  {attack.likelihood}")
    if attack.mitre_atlas:
        print(f"  MITRE ATLAS: {', '.join(attack.mitre_atlas)}")
    else:
        print("  MITRE ATLAS: —")
    print(f"  Real case:   {attack.real_case.get('title', '—')} ({attack.real_case.get('year', '—')})")
    print(f"  Mechanics:   {attack.mechanics}")
    print(f"  Indicators:  {', '.join(attack.indicators)}")
    print(f"  Defense:     {', '.join(attack.suggested_defense)}")
    print(f"  Simulatable: {', '.join(attack.simulatable_by)}")
    print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PaySentinel Identify pillar.")
    parser.add_argument("--catalog", type=Path, default=CATALOG_PATH)
    parser.add_argument("--id", help="Show one attack by ID (e.g. PSF-014)")
    parser.add_argument("--surface", help="Filter by surface")
    parser.add_argument("--severity", help="Filter by severity")
    parser.add_argument("--likelihood", help="Filter by likelihood")
    parser.add_argument("--search", help="Free-text search")
    parser.add_argument("--atlas", help="Filter by MITRE ATLAS technique (e.g. AML.T0051)")
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Run FastAPI server on :8001 (for the web prototype)",
    )
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args(argv)

    catalog = load_catalog(args.catalog)

    if args.serve:
        return _serve(catalog, args.port)

    if args.id:
        a = get_attack(catalog, args.id)
        if not a:
            print(f"Not found: {args.id}", file=sys.stderr)
            return 1
        _print_attack(a)
        return 0

    if args.surface or args.severity or args.likelihood or args.search or args.atlas:
        for a in filter_attacks(
            catalog,
            surface=args.surface,
            severity=args.severity,
            likelihood=args.likelihood,
            text=args.search,
            atlas=args.atlas,
        ):
            _print_attack(a)
        return 0

    _print_summary(catalog)
    return 0


# ----------------------------- FastAPI ----------------------------- #


def _serve(catalog: Catalog, port: int) -> int:
    """Run a FastAPI server exposing the catalog for the web prototype."""
    try:
        from fastapi import FastAPI, HTTPException, Query
        from fastapi.middleware.cors import CORSMiddleware
        import uvicorn
    except ImportError:
        print(
            "FastAPI/uvicorn not installed. Run: pip install fastapi uvicorn",
            file=sys.stderr,
        )
        return 1

    app = FastAPI(title="PaySentinel — Threat Landscape API", version=catalog.version)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/catalog")
    def list_catalog(
        surface: str | None = None,
        severity: str | None = None,
        likelihood: str | None = None,
        search: str | None = None,
        atlas: str | None = None,
    ) -> dict[str, Any]:
        items = [
            {**asdict(a), "ai_brief": ai_brief(a)}
            for a in filter_attacks(
                catalog,
                surface=surface,
                severity=severity,
                likelihood=likelihood,
                text=search,
                atlas=atlas,
            )
        ]
        return {
            "version": catalog.version,
            "count": len(items),
            "stats": catalog.stats,
            "surfaces": catalog.surfaces,
            "items": items,
        }

    @app.get("/catalog/{attack_id}")
    def get_one(attack_id: str) -> dict[str, Any]:
        a = get_attack(catalog, attack_id)
        if not a:
            raise HTTPException(status_code=404, detail="attack not found")
        return {**asdict(a), "ai_brief": ai_brief(a)}

    @app.get("/analytics/distribution")
    def analytics() -> dict[str, Any]:
        return {
            "by_surface": surface_distribution(catalog),
            "by_severity": severity_distribution(catalog),
            "by_likelihood": likelihood_distribution(catalog),
            "atlas_coverage": atlas_coverage(catalog),
        }

    @app.get("/analytics/heatmap")
    def heatmap() -> dict[str, Any]:
        """ATLAS tactic × severity matrix for the heatmap visualization."""
        matrix: dict[str, dict[str, int]] = {}
        for a in catalog.attacks:
            for t in a.mitre_atlas:
                matrix.setdefault(t, {"critical": 0, "high": 0, "medium": 0, "low": 0})
                matrix[t][a.severity] = matrix[t].get(a.severity, 0) + 1
        return {"matrix": matrix}

    uvicorn.run(app, host="0.0.0.0", port=port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
