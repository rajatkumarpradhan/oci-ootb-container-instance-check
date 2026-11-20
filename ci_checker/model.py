"""Data model + export loading for the container instance audit."""

from __future__ import annotations

import json
from dataclasses import dataclass


class ExportError(ValueError):
    """Raised when an export file is malformed."""


SECRET_LIKE_TOKENS = ("PASSWORD", "SECRET", "TOKEN", "API_KEY", "APIKEY", "PRIVATE_KEY")
JOB_LABELS = ("job", "batch", "cron", "task")
PROD_LABELS = ("prod", "production")


def is_secret_like(name: str) -> bool:
    upper = name.upper()
    return any(tok in upper for tok in SECRET_LIKE_TOKENS)


def has_label(labels: tuple, candidates: tuple) -> bool:
    lowered = [x.lower() for x in labels]
    return any(c in x for x in lowered for c in candidates)


def image_tag(image_url: str) -> str:
    """Return the tag part of an image reference, or '' when none is recorded."""
    tail = image_url.rsplit("/", 1)[-1]
    if ":" in tail:
        return tail.rsplit(":", 1)[-1]
    return ""


@dataclass(frozen=True)
class Container:
    name: str
    image_url: str
    env: tuple = ()  # tuple of (name, value) pairs as recorded

    def unpinned(self) -> bool:
        return image_tag(self.image_url) in ("", "latest")

    def secret_env_names(self) -> list:
        return [k for k, v in self.env if is_secret_like(k) and v]


@dataclass(frozen=True)
class Instance:
    name: str
    labels: tuple            # workload labels recorded in the export, e.g. ("prod",), ("batch",)
    restart_policy: str      # ALWAYS | NEVER | ON_FAILURE
    shutdown_timeout: int    # graceful shutdown timeout in seconds, 0 = unset/default
    containers: tuple = ()


def load_export(path: str) -> tuple:
    with open(path, "r", encoding="utf-8") as fh:
        try:
            raw = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ExportError(f"{path}: not valid JSON: {exc}") from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("instances"), list):
        raise ExportError(f"{path}: top level must be an object with an 'instances' list")
    out = []
    for i, r in enumerate(raw["instances"]):
        where = f"instances[{i}]"
        for req in ("name", "restart_policy"):
            if req not in r:
                raise ExportError(f"{where}: missing required field {req!r}")
        policy = r["restart_policy"].upper()
        if policy not in ("ALWAYS", "NEVER", "ON_FAILURE"):
            raise ExportError(f"{where}.restart_policy: unknown policy {r['restart_policy']!r}")
        containers = []
        for j, c in enumerate(r.get("containers", [])):
            cwhere = f"{where}.containers[{j}]"
            for req in ("name", "image_url"):
                if req not in c:
                    raise ExportError(f"{cwhere}: missing required field {req!r}")
            env = c.get("env", {})
            if not isinstance(env, dict):
                raise ExportError(f"{cwhere}.env: must be an object of name:value pairs")
            containers.append(Container(name=c["name"], image_url=c["image_url"], env=tuple(env.items())))
        timeout = r.get("shutdown_timeout", 0)
        if not isinstance(timeout, int) or timeout < 0:
            raise ExportError(f"{where}.shutdown_timeout: must be a non-negative integer")
        out.append(Instance(
            name=r["name"],
            labels=tuple(r.get("labels", [])),
            restart_policy=policy,
            shutdown_timeout=timeout,
            containers=tuple(containers),
        ))
    return tuple(out)
