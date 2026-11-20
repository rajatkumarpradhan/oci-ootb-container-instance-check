# oci-ootb-container-instance-check

**Category: built-in OCI services project (OOTB).** The custom portfolio project in this
pair is `oci-capacity-reservation-audit`.

## Which built-in OCI services this wires

- **OCI Container Instances** (`oci_container_instances_container_instance`): the built-in
  serverless container runtime. The service applies a **container restart policy**
  (`ALWAYS` is the default per OCI docs), a **graceful shutdown timeout** (default **0
  seconds**), plain `environment_variables`, and `image_url` values whose tag defaults to
  `latest` when omitted. Every default above is convenient and silently risky.

## Custom code vs native config

- **Native config**: `terraform/` declares one container instance the way a careful team
  would: pinned image tag, explicit restart policy, explicit graceful shutdown timeout, no
  secrets in environment variables. **Template only - NOT plan/apply validated** (no live
  tenancy).
- **Custom code**: `ci_checker/` audits an offline JSON export of container instances
  against four gaps the service accepts silently.

## The rules

| Rule | Severity | Fires when |
| ---- | -------- | ---------- |
| CINS001 | HIGH | A container's recorded env vars include a **secret-looking name** (`PASSWORD`, `SECRET`, `TOKEN`, `API_KEY`) with a plaintext value - OCI docs pass env vars in cleartext; secrets belong in Vault. Review flag on naming, not proof of exposure. |
| CINS002 | MEDIUM | An instance labeled as a **job/batch** workload runs restart policy `ALWAYS` (the service default) - a completed task would restart forever. |
| CINS003 | MEDIUM | An instance labeled **prod** runs a container whose `image_url` has no tag or tag `latest` - deploys are not reproducible from this reference (OCI defaults a missing tag to `latest`). |
| CINS004 | LOW | Graceful shutdown timeout is 0 or unrecorded (the service default) - containers are hard-killed on stop. |

Exit code: `2` on any HIGH, `1` on MEDIUM/LOW only, `0` when clean.

## Run it

```bash
python -m ci_checker.cli samples/instances_messy.json   # exits 2, all 4 rules fire
python -m ci_checker.cli samples/instances_clean.json   # exits 0
python -m unittest discover -s tests -v                 # 20 tests, stdlib only
```

## Honest limits

- **Offline audit**: the JSON export is synthetic; nothing calls the OCI API.
- CINS001/CINS003 are review flags on naming heuristics (secret-like env names,
  `job`/`batch`/`prod` labels), not proof of a live misconfiguration.
- Restart-policy and shutdown-timeout defaults are from the OCI Container Instances docs as
  of Nov 2026; verify current service behavior before acting.
- The Terraform template is illustrative and has **not** been plan/apply validated.
- No live tenancy was touched.

## Project status

Built as a daily OOTB project. 20 unit tests, green locally and in CI. Free tier only; no
live cloud calls, no spend.
