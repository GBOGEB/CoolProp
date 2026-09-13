# Mission I W4 — CI queue pressure evidence

This note binds the L6 trigger-scope change to observed GitHub Actions pressure rather than a speculative optimization.

## Observation

Captured during parallel Mission I Wave 4 execution on 2026-09-13:

- repository-wide queued workflow runs: **31**;
- repository-wide in-progress workflow runs: **11**;
- total active workflow runs at the observation point: **42**.

The documentation-Docker repair branch `mission/i-w4-first-red-docs-docker` alone had:

- **13 queued** workflow runs;
- **6 in progress** workflow runs;
- **19 active** workflow runs;

while its intended target was one documentation-base Docker verification job.

The Python wheel compatibility branch `mission/i-w4-python-wheel-compat` had **13 queued workflows before the Python wheel matrix itself had begun executing**.

This is direct evidence of the Mission-I scheduling failure mode:

`FAST / bounded verification -> waits behind unrelated HEAVY fan-out`.

## Bounded change

The companion change only keeps the HEAVY Python wheel matrix off pull requests whose changed paths are confined to:

- `qps/**` mission-control/evidence surfaces;
- QPS-specific workflows;
- documentation Docker base/image surfaces.

All ordinary product, Python binding, build-system, core source, packaging and dependency changes continue to trigger the wheel matrix.

## Victory / DoD

1. A QPS-control-only pull request does not start `Python cibuildwheel`.
2. A documentation-base-only pull request does not start `Python cibuildwheel`.
3. A Python/core/build/package change still starts `Python cibuildwheel`.
4. No product test is marked green merely because it did not run; skipped-by-path is a scheduling decision, not evidence of product correctness.
5. FAST lane queue pressure drops without weakening evidence requirements for changed product surfaces.

## Next performance layer

This is intentionally narrower than a repository-wide workflow routing rewrite. After measured validation, the same evidence-first method can classify other wrappers into:

- mandatory cross-cutting gates;
- path-owned FAST checks;
- path-owned HEAVY checks;
- licensed/secret gates;
- release-only/publish-only gates.

Only then should broader trigger topology or dedicated runner-pool changes be promoted.
