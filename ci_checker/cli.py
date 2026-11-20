"""python -m ci_checker.cli EXPORT"""

from __future__ import annotations

import argparse
import sys

from .model import ExportError, load_export
from .rules import exit_code, run_all


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="container-instance-check",
        description="Audit an offline export of OCI Container Instances for silent-default and hygiene gaps.",
    )
    p.add_argument("export", help="path to the JSON export")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        instances = load_export(args.export)
    except ExportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    findings = run_all(instances)
    n_containers = sum(len(i.containers) for i in instances)
    print(
        f"Container instance audit - {len(instances)} instance(s), "
        f"{n_containers} container(s), {len(findings)} finding(s)"
    )
    for x in findings:
        print(f"[{x.severity:6s}] {x.rule} instance={x.instance}")
        print(f"         {x.detail}")
    code = exit_code(findings)
    print({0: "RESULT: clean", 1: "RESULT: warnings only", 2: "RESULT: HIGH findings present"}[code])
    return code


if __name__ == "__main__":
    raise SystemExit(main())
