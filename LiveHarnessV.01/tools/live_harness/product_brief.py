from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any
import re

CONTROL_PLANE_TERMS = [
    "NVIDIA" + "_" + "API" + "_" + "KEY",
    "GH" + "_" + "TOKEN",
    "GITHUB" + "_" + "TOKEN",
    "Open" + "AI",
    "chat" + "." + "completions",
    "reasoning" + "_" + "budget",
    "model tier",
    "NVIDIA model",
    "nemotron",
    "workflow" + "_" + "dispatch",
    "secrets" + "[",
    "LIVEHARNESS" + "_" + "RUN" + "_" + "DIR",
    "LIVEHARNESS" + "_" + "RUN" + "_" + "ID",
]

PRIVATE_HINTS = [
    "preserve logs",
    "partial outputs",
    "run deterministic",
    "update capability ledger",
    "nvidia",
    "api key",
    "workflow",
    "github",
    "liveharness",
    "model",
    "llm",
    "commit artifacts",
]

@dataclass
class ProductBrief:
    mode: str
    public_title: str
    public_goal: str
    public_summary: str
    product_features: list[str]
    private_harness_notes: list[str]
    blocked_public_terms: list[str]
    raw_has_control_terms: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _parse_frontmatter(raw: str) -> tuple[dict[str, Any], str]:
    text = raw.strip()
    if not text.startswith("---"):
        return {}, raw
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, raw
    _, front, body = parts
    data: dict[str, Any] = {}
    current_key: str | None = None
    for line in front.splitlines():
        if not line.strip():
            continue
        if line.startswith("  -") and current_key:
            data.setdefault(current_key, []).append(line.split("-", 1)[1].strip())
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip().strip('"')
            current_key = key
            data[key] = value if value else []
    return data, body.strip()


def sanitize_public_text(value: str) -> str:
    text = value or ""
    for term in CONTROL_PLANE_TERMS:
        text = re.sub(re.escape(term), "", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(NVIDIA|OpenAI|LLM|model tiers?|workflow|GitHub Actions|API key)\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _is_private_line(line: str) -> bool:
    low = line.lower()
    return any(hint in low for hint in PRIVATE_HINTS)


def _infer_title(body: str, explicit: str | None = None) -> str:
    if explicit:
        return sanitize_public_text(explicit) or "NexusRealtime Build"
    for line in body.splitlines():
        stripped = line.strip("# \t")
        if stripped and not _is_private_line(stripped):
            return sanitize_public_text(stripped)[:80] or "NexusRealtime Build"
    low = body.lower()
    if "minecraft" in low or "voxel" in low:
        return "Voxel Domain Builder"
    if "bubble" in low or "dsk" in low:
        return "DSK Bubble Kit Builder"
    if "sequence" in low or "gate" in low:
        return "Sequence Gate Kit Builder"
    if "kit" in low:
        return "NexusRealtime Kit Builder"
    return "NexusRealtime Build"


def _features_from_body(body: str) -> list[str]:
    features: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("-"):
            item = sanitize_public_text(stripped.lstrip("- ").strip())
            if item and not _is_private_line(item):
                features.append(item)
    if features:
        return list(dict.fromkeys(features))[:12]
    low = body.lower()
    if "minecraft" in low or "voxel" in low:
        return ["voxel terrain", "state-scoped movement", "build and break domain actions", "inventory block palette", "debug host state"]
    if "dsk" in low or "domain" in low:
        return ["domain bubble editor", "owned state panel", "commands and events panel", "idempotency key editor", "sequence and gate view", "debug host panel"]
    return ["NexusRealtime kit composition surface", "debug host panel", "state-first designer view"]


def _public_goal(body: str, explicit: str | None = None) -> str:
    if explicit:
        return sanitize_public_text(explicit)
    lines = []
    for line in body.splitlines():
        stripped = line.strip().strip("#")
        if not stripped or stripped.startswith("-") or _is_private_line(stripped):
            continue
        lines.append(stripped)
    goal = " ".join(lines[:3])
    if not goal:
        low = body.lower()
        if "minecraft" in low or "voxel" in low:
            goal = "Build a browser-playable voxel world tool for testing NexusRealtime Domain Service Kit boundaries."
        elif "dsk" in low:
            goal = "Build a browser tool for designing NexusRealtime Domain Service Kits."
        else:
            goal = "Build a NexusRealtime designer-facing kit composition tool."
    return sanitize_public_text(goal)[:500]


def make_brief(raw_prompt: str, default_mode: str = "kit-builder") -> ProductBrief:
    front, body = _parse_frontmatter(raw_prompt)
    mode = str(front.get("mode") or default_mode or "kit-builder")
    public_title = _infer_title(body, str(front.get("public_title")) if front.get("public_title") else None)
    public_goal = _public_goal(body, str(front.get("public_goal")) if front.get("public_goal") else None)
    if isinstance(front.get("product_features"), list):
        features = [sanitize_public_text(str(item)) for item in front["product_features"]]
    else:
        features = _features_from_body(body)
    features = [item for item in features if item]
    private_notes = list(front.get("private_harness_notes", [])) if isinstance(front.get("private_harness_notes"), list) else []
    for line in body.splitlines():
        stripped = line.strip("- #\t")
        if stripped and _is_private_line(stripped):
            private_notes.append(stripped)
    raw_low = raw_prompt.lower()
    has_control = any(term.lower() in raw_low for term in CONTROL_PLANE_TERMS) or any(h in raw_low for h in PRIVATE_HINTS)
    return ProductBrief(mode, public_title, public_goal, public_goal, list(dict.fromkeys(features))[:12], list(dict.fromkeys([str(x) for x in private_notes]))[:20], CONTROL_PLANE_TERMS, bool(has_control))


def product_prompt(raw_prompt: str, default_mode: str = "kit-builder") -> str:
    brief = make_brief(raw_prompt, default_mode)
    return "\n".join([f"Title: {brief.public_title}", f"Goal: {brief.public_goal}", "Features:", *[f"- {feature}" for feature in brief.product_features]])
