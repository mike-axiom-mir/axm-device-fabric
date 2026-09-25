# Require explicit device availability and finite evidence

Date: 2026-09-25 UTC

Base commit: `4f822c9e9d2e41015aac6d1ac9e3c61b8ad0aa38`

Status: experimental repair, not merged or promoted.

## Observed failure

A capability with available="false", granted authority and a matching operation passed request admission. Nonfinite observations also acquired a state digest. The regression suite failed before the repair.

## Repair

Availability must be a boolean; canonical evidence serialization rejects nonfinite numbers. Existing unavailable, unknown-authority and stale-state blockers remain in place.

## Verification

Command: `PYTHONPATH=src:. python -m unittest discover -s tests -v`

12 tests passed.

Regression tests exercise invalid input and valid-state continuity. The full repository command above passed on the repaired working tree. No production-readiness, deployment, or CANON claim is made.

Package metadata now declares MPL-2.0, matching the existing LICENSE and LICENSE_BOUNDARY.md. No license text or historical grant was changed.
