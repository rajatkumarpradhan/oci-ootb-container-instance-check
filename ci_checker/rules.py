"""CINS001-CINS004 rules."""

from __future__ import annotations

from dataclasses import dataclass

from .model import JOB_LABELS, PROD_LABELS, has_label


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str  # HIGH | MEDIUM | LOW
    instance: str
    detail: str


def rule_secret_env(instances: tuple) -> list:
    """CINS001 HIGH: plaintext secret-looking env var recorded."""
    out = []
    for inst in instances:
        for c in inst.containers:
            names = c.secret_env_names()
            if names:
                out.append(
                    Finding("CINS001", "HIGH", inst.name,
                            f"container {c.name} records plaintext env var(s) {names} with secret-looking "
                            f"name(s); env vars are cleartext - review and move these to Vault if real")
                )
    return out


def rule_job_restart_always(instances: tuple) -> list:
    """CINS002 MEDIUM: job/batch-labeled instance with restart policy ALWAYS."""
    return [
        Finding("CINS002", "MEDIUM", inst.name,
                "job/batch-labeled workload runs restart policy ALWAYS (the service default); "
                "a completed task would restart forever - ON_FAILURE or NEVER fits jobs")
        for inst in instances
        if has_label(inst.labels, JOB_LABELS) and inst.restart_policy == "ALWAYS"
    ]


def rule_prod_unpinned_image(instances: tuple) -> list:
    """CINS003 MEDIUM: prod-labeled instance with an unpinned image reference."""
    out = []
    for inst in instances:
        if not has_label(inst.labels, PROD_LABELS):
            continue
        for c in inst.containers:
            if c.unpinned():
                out.append(
                    Finding("CINS003", "MEDIUM", inst.name,
                            f"prod-labeled instance runs container {c.name} from {c.image_url!r} with no "
                            f"immutable tag; a missing tag defaults to 'latest' - deploys are not reproducible")
                )
    return out


def rule_no_graceful_shutdown(instances: tuple) -> list:
    """CINS004 LOW: graceful shutdown timeout 0/unrecorded (the service default)."""
    return [
        Finding("CINS004", "LOW", inst.name,
                "graceful shutdown timeout is 0/unrecorded (the service default); "
                "containers are hard-killed on stop")
        for inst in instances if inst.shutdown_timeout == 0
    ]


ALL_RULES = (
    rule_secret_env,
    rule_job_restart_always,
    rule_prod_unpinned_image,
    rule_no_graceful_shutdown,
)

_SEVERITY_RANK = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def run_all(instances: tuple) -> list:
    findings = []
    for rule in ALL_RULES:
        findings.extend(rule(instances))
    findings.sort(key=lambda x: (_SEVERITY_RANK[x.severity], x.rule, x.instance))
    return findings


def exit_code(findings: list) -> int:
    if any(f.severity == "HIGH" for f in findings):
        return 2
    if findings:
        return 1
    return 0
