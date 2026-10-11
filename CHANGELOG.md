# Changelog

## v0.1.1 (2026-10-11) — self-review revision (iteration 2)

- **Clarity (+~30%)**: Quickstart rewritten with explicit timings and the warning that `qa` takes a single card (not the enumerate wrapper) — the #1 misuse found in self-review.
- **Completeness**: added Limits note on second-order "green-tint drift" (gate-passed but bland output) per rule 16.
- **Correctness**: fixed schema version constant to v1.1 and added a self-test (C5–C8) for CLI-level corrupted-JSON and unknown-dictionary handling.

## v0.1.0 (2026-10-11) — initial draft

- 35-style × 9-grammar dictionaries, `compose` / `enumerate` / `qa` CLI.
- Delivery gate `qa_check` with exact failure lists.
- `self_test.py` with functional / error-path / edge-case classes (18 checks).
