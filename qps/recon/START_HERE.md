# QPS DARKLAND RECON — CoolProp START HERE

This directory is a reconnaissance overlay. It does **not** redefine upstream CoolProp and it does not make the fork `master` a QPS-owned codebase.

## Five things to understand before touching the repo

1. **Ownership boundary** — `GBOGEB/CoolProp` is a foreign fork of `CoolProp/CoolProp`. The frozen fork baseline is `a3c743026521ff557f8c2e85701c726898b00e0b`; reconnaissance changes belong on `recon/qps-coolprop`, not `master`.
2. **Upstream drift** — at mission start, upstream `master` was observed at `d5b0cfb51cd9a9343284cc5af8ebd6a8bd0eecc0`, 513 commits after the fork point. Sync and QPS adaptation are separate concerns.
3. **Public contract** — start with `include/CoolProp.h`, then `src/CoolProp.cpp`. `PropsSI` / `PropsSImulti` are the high-level property contracts; `AbstractState::factory` selects the backend and defaults unspecified fluids to HEOS.
4. **Helium path** — follow `PropsSI -> _PropsSImulti -> AbstractState::factory -> HEOS/Helmholtz -> dev/fluids/Helium.json`. The helium model cites `OrtizVega-JPCRD-2019`.
5. **2 K authority boundary** — helium saturation/ancillary data expose a lower boundary around 2.1768 K. A numerical CoolProp result at 2 K is therefore evidence to investigate, not automatic permission to replace HEPAK. QPS promotion requires an independent HEPAK cross-check.

## Mission files

- `MISSION.yaml` — scope, state, victory chain and stop rules.
- `CREW.yaml` — worker duties, secondary objectives and explicit hand-offs.
- `ORCHESTRATOR_STATE.yaml` — current BG/CG and evidence-driven routing.
- `REPO_CARD.yaml` — compact classification, upstream and QPS relevance.
- `probe_qplant_helium.py` — Smoker executable for A/B/D/W and 2 K boundary.
- `.github/workflows/qps_darkland_coolprop.yml` — repo-native build and exact-run receipt.

## Current execution route

`PARTIAL -> CG-HELIUM-PROBE -> Smoker -> first red classification -> Doctor | Dockter | Scientist | Governor -> re-smoke -> Evidence Keeper`

No result becomes QPS SSOT merely because this workflow passes.
