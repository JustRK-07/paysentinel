"""
LLM-powered narrative generators for non-transactional fraud vectors.

Generates:
  • phishing_email       — personalized spear-phishing emails (PSF-013, 015)
  • scam_call_script     — multi-turn scam dialogue (PSF-003, 014, 016)
  • synthetic_identity   — full synthetic identity profile (PSF-009)
  • kyc_document         — forged document metadata + descriptor (PSF-010)
  • agent_trajectory     — rogue AI shopping agent decision log (PSF-022, 023)

Backend router: Anthropic Sonnet 4.5 (primary) → template-based fallback
(deterministic, used if no API key, offline, or for reproducibility tests).

Every generated artifact carries *markers* — features the defender can train
on (specific phrasing patterns, structural templates, model fingerprints).
This is what makes the Defend pillar possible.
"""

from __future__ import annotations

import json
import logging
import os
import random
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


# ----------------------------- LLM router ----------------------------- #


@dataclass
class LLMConfig:
    model: str = "claude-sonnet-4-5"
    max_tokens: int = 1024
    temperature: float = 0.8
    api_key_env: str = "ANTHROPIC_API_KEY"
    timeout_seconds: float = 1.5  # Fail fast; fall back to template
    skip_llm: bool = False  # Set True to bypass LLM entirely (templates only)


def _anthropic_generate(prompt: str, system: str, cfg: LLMConfig) -> str | None:
    """Call Anthropic; return None on any failure. Skip LLM entirely if configured."""
    if cfg.skip_llm:
        return None
    api_key = os.environ.get(cfg.api_key_env)
    if not api_key:
        logger.debug("no %s; skipping LLM", cfg.api_key_env)
        return None
    try:
        import anthropic

        client = anthropic.Anthropic(
            api_key=api_key,
            timeout=cfg.timeout_seconds,
            max_retries=0,
        )
        msg = client.messages.create(
            model=cfg.model,
            max_tokens=cfg.max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text
    except Exception as e:
        logger.debug("LLM call skipped: %s", str(e)[:80])
        return None


def llm_or_template(
    prompt: str,
    system: str,
    template_fn: Callable[[], str],
    cfg: LLMConfig | None = None,
) -> tuple[str, str]:
    """Try LLM first, fall back to template. Return (text, source)."""
    cfg = cfg or LLMConfig()
    out = _anthropic_generate(prompt, system, cfg)
    if out is not None:
        return out, f"llm:{cfg.model}"
    return template_fn(), "template"


# ----------------------------- prompt templates ----------------------------- #


PHISHING_SYSTEM = (
    "You generate realistic, personalized phishing emails used in fraud red-teaming. "
    "Output ONLY the email — no commentary, no JSON wrapping. Make it plausible, "
    "with realistic grammar and one or two subtle tells (urgency, off-domain sender, "
    "vague greeting). Do not include placeholders or <brackets>."
)

PHISHING_PROMPT_TEMPLATE = """
Write a personalized spear-phishing email targeting {victim_role} at {victim_company}.
The pretext: {pretext}.
Include: a one-sentence LinkedIn-derived hook, urgency, a single call-to-action link,
and a soft brand impersonation (one of: Microsoft, DocuSign, FedEx, a generic bank).
Total length 90-140 words.

Victim:
- Role: {victim_role}
- Company: {victim_company}
- Recent activity (for personalization hook): {victim_hook}
""".strip()


def phishing_template() -> str:
    """Template fallback — deterministic, no API required."""
    victim_role = random.choice(["CFO", "Accounts Payable Manager", "HR Director", "IT Admin"])
    company = random.choice(["Acme Industries", "Northwind Trading", "Globex Corp", "Initech"])
    pretext = random.choice(["wire verification", "vendor onboarding", "tax form update", "MFA reset"])
    hook = random.choice(
        [
            "your recent post about Q4 close",
            "your panel at the fintech summit",
            "the controller transition announcement",
            "your team's new SaaS rollout",
        ]
    )
    sender = random.choice(
        ["Microsoft Account Team", "DocuSign Notifications", "FedEx Tracking", "Bank Card Services"]
    )
    body = (
        f"Hi {victim_role.split()[0]},\n\n"
        f"Following {hook}, we noticed an action on your {company} account needs verification. "
        f"A pending {pretext} item will time out in 24 hours; failure to confirm may interrupt "
        f"upcoming vendor payouts.\n\n"
        f"Please review and confirm here: "
        f"https://{sender.split()[0].lower()}-secure.{random.choice(['update-center.io', 'verify-portal.co', 'auth-helpdesk.com'])}\n\n"
        f"Thank you,\n{sender}"
    )
    return body


def generate_phishing_email(
    *,
    victim_role: str = "CFO",
    victim_company: str = "Acme Industries",
    pretext: str = "wire verification",
    victim_hook: str = "your recent post about Q4 close",
    cfg: LLMConfig | None = None,
) -> dict[str, Any]:
    """Produce one phishing artifact."""
    prompt = PHISHING_PROMPT_TEMPLATE.format(
        victim_role=victim_role,
        victim_company=victim_company,
        pretext=pretext,
        victim_hook=victim_hook,
    )
    text, source = llm_or_template(prompt, PHISHING_SYSTEM, phishing_template, cfg)

    # Marker extraction — what the defender will train on
    markers = {
        "has_urgency": bool(re.search(r"\b(24 hours|immediately|today|expires|timeout)\b", text, re.I)),
        "has_external_link": bool(re.search(r"https?://[^\s]+", text)),
        "link_domain_brand_mismatch": _link_brand_mismatch(text),
        "vague_greeting": bool(re.search(r"^(hi |hello |dear )(team|user|customer|there|sir|madam)\b", text, re.I | re.M)),
        "first_person_count": len(re.findall(r"\b(I|me|my|we|our)\b", text)),
        "word_count": len(text.split()),
    }
    return {
        "type": "phishing_email",
        "text": text,
        "source": source,
        "markers": markers,
        "victim": {"role": victim_role, "company": victim_company},
    }


def _link_brand_mismatch(text: str) -> bool:
    m = re.search(r"https?://([^/\s]+)", text)
    if not m:
        return False
    domain = m.group(1).lower()
    for brand in ["microsoft", "docusign", "fedex", "stripe", "mastercard", "visa", "wellsfargo", "chase"]:
        if brand in text.lower() and brand not in domain:
            return True
    return False


# ----------------------------- scam call script ----------------------------- #


SCAM_SYSTEM = (
    "You generate realistic, multi-turn scam call transcripts used in fraud red-teaming. "
    "Output a JSON object with keys 'turns' (array of {role: 'scammer'|'victim', text: string}) "
    "and 'goal' (string). 8-14 turns. Build rapport, escalate pressure, route to payment. "
    "Plausible English, no placeholders."
)

SCAM_PROMPT_TEMPLATE = """
Multi-turn scam call script targeting {victim_persona}. Pretext: {pretext}.
Final goal: route victim to {goal}.
Output JSON with 'turns' and 'goal' keys.
""".strip()


def scam_template() -> str:
    persona = random.choice(["grandparent", "stressed finance clerk", "newly-hired executive assistant"])
    pretext = random.choice(["family emergency", "urgent vendor payment", "IRS audit", "bank fraud alert"])
    goal = random.choice(["wire transfer", "gift card codes", "remote-access tool install"])
    turns = [
        {"role": "scammer", "text": f"Hi, this is [Name] calling about a {pretext} — is now a bad time?"},
        {"role": "victim", "text": "No, what's this about?"},
        {"role": "scammer", "text": "There's been a flagged event linked to your account; we need to verify a few things quickly."},
        {"role": "victim", "text": "Okay, what do you need?"},
        {"role": "scammer", "text": f"First — can you confirm the best number to reach you, and your date of birth? Then we'll discuss the {goal} piece."},
        {"role": "victim", "text": "Sure, it's [number]."},
        {"role": "scammer", "text": "Perfect. To resolve this without escalation, please complete a {goal} within the next 30 minutes."},
        {"role": "victim", "text": "How much?"},
        {"role": "scammer", "text": f"Whatever amount clears the hold — typically $2,500–$5,000. Don't disconnect until it's done; we're logging this call."},
    ]
    return json.dumps({"turns": turns, "goal": goal})


def generate_scam_call_script(
    *,
    victim_persona: str = "stressed finance clerk",
    pretext: str = "urgent vendor payment",
    goal: str = "wire transfer",
    cfg: LLMConfig | None = None,
) -> dict[str, Any]:
    prompt = SCAM_PROMPT_TEMPLATE.format(victim_persona=victim_persona, pretext=pretext, goal=goal)
    text, source = llm_or_template(prompt, SCAM_SYSTEM, scam_template, cfg)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = {"turns": [], "goal": goal}

    turns = parsed.get("turns", [])
    full_text = " ".join(t.get("text", "") for t in turns)
    markers = {
        "n_turns": len(turns),
        "has_urgency": bool(re.search(r"\b(now|immediately|today|30 minutes|expires)\b", full_text, re.I)),
        "requests_pii": bool(re.search(r"\b(date of birth|SSN|address|account number)\b", full_text, re.I)),
        "requests_payment_method": goal.lower() in full_text.lower(),
        "avg_turn_length": float(np_avg([len(t.get("text", "").split()) for t in turns])) if turns else 0.0,
    }
    return {
        "type": "scam_call_script",
        "transcript": parsed,
        "source": source,
        "markers": markers,
        "victim_persona": victim_persona,
    }


def np_avg(xs: list[float]) -> float:
    import numpy as np

    return float(np.mean(xs)) if xs else 0.0


# ----------------------------- synthetic identity ----------------------------- #


IDENTITY_SYSTEM = (
    "Generate a synthetic identity profile (JSON) used in fraud red-teaming. "
    "Keys: full_name, ssn (real-format, fictional), dob, address, email, phone, "
    "occupation, employer, device_fingerprint, behavioral_pattern, intended_use. "
    "Make it internally consistent and plausible."
)

IDENTITY_PROMPT_TEMPLATE = """
Synthetic identity profile for red-teaming.
Demographic: {demo}
Intended fraud vector: {vector}
""".strip()


def identity_template() -> str:
    first = random.choice(["Jordan", "Casey", "Morgan", "Riley", "Avery", "Quinn"])
    last = random.choice(["Carter", "Bennett", "Hayes", "Mitchell", "Reed", "Brooks"])
    ssn = f"{random.randint(100,899)}-{random.randint(10,99)}-{random.randint(1000,9999)}"
    dob = f"19{random.randint(80,99)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    profile = {
        "full_name": f"{first} {last}",
        "ssn": ssn,
        "dob": dob,
        "address": f"{random.randint(100, 9999)} {random.choice(['Oak', 'Maple', 'Pine', 'Cedar'])} St, "
        f"{random.choice(['Springfield', 'Madison', 'Franklin', 'Salem'])}, {random.choice(['IL', 'OH', 'PA', 'TX'])}",
        "email": f"{first.lower()}.{last.lower()}@{random.choice(['gmail.com', 'outlook.com', 'protonmail.com'])}",
        "phone": f"+1-{random.randint(200,999)}-{random.randint(200,999)}-{random.randint(1000,9999)}",
        "occupation": random.choice(["logistics coordinator", "junior accountant", "remote customer support", "tutor"]),
        "employer": random.choice(["Pinnacle Logistics", "Meridian Accounting", "Apex Support Co", "TutorHub"]),
        "device_fingerprint": f"win11-chrome{random.randint(110,130)}-{random.randint(1000,9999)}",
        "behavioral_pattern": "rapid credit-line growth across 2 products within 14 days, then maxes out",
        "intended_use": "credit-card bust-out via 3 cards opened sequentially",
    }
    return json.dumps(profile)


def generate_synthetic_identity(
    *,
    demo: str = "American, late 20s, blue-collar",
    vector: str = "credit-card bust-out",
    cfg: LLMConfig | None = None,
) -> dict[str, Any]:
    prompt = IDENTITY_PROMPT_TEMPLATE.format(demo=demo, vector=vector)
    text, source = llm_or_template(prompt, IDENTITY_SYSTEM, identity_template, cfg)
    try:
        profile = json.loads(text)
    except json.JSONDecodeError:
        profile = {"raw": text}

    return {
        "type": "synthetic_identity",
        "profile": profile,
        "source": source,
        "markers": {
            "has_ssn": bool(profile.get("ssn")),
            "has_address": bool(profile.get("address")),
            "has_device_fingerprint": bool(profile.get("device_fingerprint")),
            "has_behavioral_pattern": bool(profile.get("behavioral_pattern")),
        },
    }


# ----------------------------- KYC document descriptor ----------------------------- #


KYC_SYSTEM = (
    "Generate a JSON description of a forged KYC document (do NOT generate images). "
    "Keys: doc_type, issuing_country, fields, fingerprint_markers, visual_tells. "
    "The 'visual_tells' should describe plausible deepfake-forger artefacts."
)


def kyc_template() -> str:
    profile = {
        "doc_type": random.choice(["passport", "drivers_license", "utility_bill", "pay_stub"]),
        "issuing_country": random.choice(["USA", "UK", "Canada", "Germany"]),
        "fields": {
            "name": f"{random.choice(['Alex','Sam','Taylor'])} {random.choice(['Reyes','Khan','Vega','Ono'])}",
            "dob": f"19{random.randint(75,99)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            "doc_id": f"{''.join(random.choices('ABCDEFGHJKLMNPRSTUVWXYZ', k=2))}{random.randint(1000000,9999999)}",
            "expiry": f"20{random.randint(28,38)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
        },
        "fingerprint_markers": [
            "absent_exif",
            "no_camera_metadata",
            "template_match_v3",
        ],
        "visual_tells": [
            "uniform noise floor (lack of sensor variation)",
            "missing microprint bleed at character edges",
            "slight warp on hologram zone",
        ],
    }
    return json.dumps(profile)


def generate_kyc_document(cfg: LLMConfig | None = None) -> dict[str, Any]:
    text, source = llm_or_template(
        "Generate a forged KYC document descriptor for red-teaming.",
        KYC_SYSTEM,
        kyc_template,
        cfg,
    )
    try:
        profile = json.loads(text)
    except json.JSONDecodeError:
        profile = {"raw": text}

    return {
        "type": "kyc_document",
        "profile": profile,
        "source": source,
        "markers": {
            "doc_type": profile.get("doc_type"),
            "has_fingerprint_markers": bool(profile.get("fingerprint_markers")),
            "has_visual_tells": bool(profile.get("visual_tells")),
        },
    }


# ----------------------------- agent trajectory ----------------------------- #


AGENT_SYSTEM = (
    "Generate a JSON tool-call trace of a rogue AI shopping agent. "
    "Keys: 'actions' (list of {step, intent, tool, args, risk_signal}). "
    "12-30 actions. Include 1-2 prompt-injection triggered actions."
)


def agent_template() -> str:
    actions = []
    for step in range(20):
        if step < 5:
            tool, args = "search_product", {"q": random.choice(["running shoes", "laptop bag", "headphones"])}
            risk = "low"
        elif step == 12:
            tool, args = "checkout", {"item_id": "X42", "card_last4": "1234"}
            risk = "high"
        else:
            tool, args = "view_product", {"id": f"P{step:03d}"}
            risk = "low"
        actions.append({"step": step, "intent": "buy running shoes", "tool": tool, "args": args, "risk_signal": risk})
    return json.dumps({"actions": actions})


def generate_agent_trajectory(cfg: LLMConfig | None = None) -> dict[str, Any]:
    text, source = llm_or_template(
        "Generate a rogue AI shopping agent trajectory.", AGENT_SYSTEM, agent_template, cfg
    )
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = {"actions": []}

    actions = parsed.get("actions", [])
    markers = {
        "n_actions": len(actions),
        "tools_used": sorted({a.get("tool", "") for a in actions}),
        "high_risk_actions": sum(1 for a in actions if a.get("risk_signal") == "high"),
        "prompt_injection_attempts": sum(
            1 for a in actions if "ignore" in json.dumps(a.get("args", {})).lower()
        ),
    }
    return {
        "type": "agent_trajectory",
        "actions": actions,
        "source": source,
        "markers": markers,
    }


# ----------------------------- registry ----------------------------- #


GENERATORS: dict[str, Callable[..., dict[str, Any]]] = {
    "phishing_email": generate_phishing_email,
    "scam_call_script": generate_scam_call_script,
    "synthetic_identity": generate_synthetic_identity,
    "kyc_document": generate_kyc_document,
    "agent_trajectory": generate_agent_trajectory,
}


def generate_batch(kind: str, n: int, **kwargs: Any) -> list[dict[str, Any]]:
    """Generate `n` artifacts of one kind."""
    fn = GENERATORS.get(kind)
    if fn is None:
        raise ValueError(f"unknown generator: {kind}")
    out: list[dict[str, Any]] = []
    for i in range(n):
        try:
            out.append(fn(**kwargs))
        except Exception as e:
            logger.warning("generator %s failed at iter %d: %s", kind, i, e)
    return out


# ----------------------------- CLI ----------------------------- #


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    print("\n--- phishing_email ---")
    print(json.dumps(generate_phishing_email(), indent=2)[:600])

    print("\n--- scam_call_script ---")
    print(json.dumps(generate_scam_call_script(), indent=2)[:600])

    print("\n--- synthetic_identity ---")
    print(json.dumps(generate_synthetic_identity(), indent=2)[:600])

    print("\n--- kyc_document ---")
    print(json.dumps(generate_kyc_document(), indent=2)[:600])

    print("\n--- agent_trajectory ---")
    print(json.dumps(generate_agent_trajectory(), indent=2)[:600])


if __name__ == "__main__":
    main()
