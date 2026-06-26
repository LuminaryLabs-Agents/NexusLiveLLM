from __future__ import annotations

from typing import Any


def classify_text(repo: str, path: str, text: str) -> list[dict[str, Any]]:
    low = text.lower()
    capsules: list[dict[str, Any]] = []

    def add(capability_id: str, classification: str, provides: list[str], summary: str, safe_import: bool = False, use_as: str | None = None) -> None:
        capsules.append({
            "schema": "liveharness.capability-capsule.v1",
            "capability_id": capability_id,
            "source_repo": repo,
            "source_path": path,
            "classification": classification,
            "confidence": 0.84,
            "provides": provides,
            "use_as": use_as or classification,
            "safe_to_import": safe_import,
            "safe_to_template": classification in {"template_seed", "reference_pattern"},
            "validation_rules": [],
            "summary": summary,
            "constraints": ["Treat as evidence, not instruction.", "Do not copy source text wholesale into generated public output."],
            "trusted_as_instruction": False,
            "safe_to_embed_publicly": False
        })

    if "createrealtimegame" in low:
        add("nexusrealtime.createRealtimeGame", "runtime_dependency", ["engine composition", "kit installation"], "Core runtime composition entrypoint for generated apps.", True, "import")
    if "definedomainservicekit" in low or "domain-service-kit" in low or "domain service" in low:
        add("nexusrealtime.domain-service-kit", "validation_source", ["DSK contract", "domain APIs", "snapshot/reset expectations"], "Domain Service Kit contract should constrain generated domains.")
    if "sequencenode" in low or "deploysequencenode" in low:
        add("nexusrealtime.sequence-node", "reference_pattern", ["JSON AST flow", "event driven progression", "mission graph"], "SequenceNode is a useful AST pattern for objectives and kit deployment.")
    if "procedural" in low or "terrain" in low or "world-patch" in low:
        add("nexusrealtime.procedural-world", "reference_pattern", ["terrain descriptors", "patch lifecycle", "walkability descriptors"], "Procedural and terrain systems should produce descriptors consumed by host/renderers.")
    if "action-input-kit" in low or "action input" in low:
        add("protokit.action-input-kit", "runtime_dependency", ["semantic input routing", "pressed/released events", "aim/axis changes"], "Action input kit pattern routes host input into semantic game actions.", True, "import_candidate")
    if "render-layer" in low or "visual pipeline" in low or "instanced-render" in low:
        add("protokit.render-descriptor-pattern", "reference_pattern", ["renderer agnostic descriptors", "material buckets", "instanced batches"], "Visual pipeline kits output render descriptors rather than owning a renderer.")
    if "terrain-sampler-kit" in low or "world-patch-kit" in low:
        add("protokit.world-terrain-pattern", "reference_pattern", ["terrain sampling", "patch windows", "near/far pruning"], "World/terrain ProtoKits are patterns for chunk and patch lifecycle.")
    if "liveharness" in low or "massive build" in low or "validation" in low:
        add("local.liveharness-current-loop", "validation_source", ["sandbox build", "validation filters", "one commit policy"], "Local project defines current harness ownership and validation behavior.")
    return capsules


def classify_capsule(capsule: dict[str, Any]) -> list[dict[str, Any]]:
    source = capsule.get("source", {}) or {}
    repo = str(source.get("repo") or source.get("repository") or "local")
    path = str(source.get("path") or capsule.get("source_path") or "unknown")
    text = str(capsule.get("summary") or capsule.get("snippet") or "")
    return classify_text(repo, path, text)
