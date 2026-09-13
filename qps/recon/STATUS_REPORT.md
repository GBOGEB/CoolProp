# QPS DARKLAND RECON — Temporal Status Report

This file is a **derived human view** of `TEMPORAL_STATUS_HOOK.yaml`. The canonical temporal hook remains authoritative; this projection is guarded against stale qualified-runtime evidence by `qps/recon/mission_i_control.py`.

## Canonical mission table

| Mission | Wave | Pulse | State | BG | CG | Crew | DoD | DoV | Next decision |
|---|---|---|---|---|---|---|---:|---:|---|
| M01 CoolProp | CONTROL + PERFORMANCE + SCIENCE | W145 exact-source accepted | EXECUTABLE / A-B-D-E-W COMPATIBILITY PROVEN | HEPAK authority; governed adapter; federation consumer | phase telemetry → FAST/HEAVY split → first true red | PM, TM, Analyst, Scientist, Engineer, QA | 78% | 0/3 | MEASURE + SPLIT + CLASSIFY |

## Qualified runtime anchor

```text
workflow     qps_w145_lkt_2kop_crosswalk.yml
run_id       34707993462
job_id       103591440737
source_sha   3f3b4b1e016a940b9b29102cf264bfac43d19e18
merge_sha    9e5927ddae4678f1c38947b261bbb21e2425c7c2
runner_id    1000256609
states       A PASS | B PASS | D PASS | E PASS | W PASS
receipt      0d788a4e0104fa6c155071704f8eda3c7e5f3a384df2406e117377c3b27d321c
authority    COMPATIBILITY_REFERENCE_CALCULATED
promotion    WITHHELD pending governed HEPAK / SAT authority
```

## Status ribbon

`M01  EXECUTABLE  | RUNTIME 100 | EVIDENCE 85 | TECH 78 | HARVEST 60 | FEDERATE 10 | DoD 78 | DoV 0/3`

## Compact bars

```text
Visibility          [###################-] 95%
Runtime proof       [####################] 100%
Evidence            [#################---] 85%
Technical confidence[################----] 78%
Repair closure      [####################] 100%
Harvest readiness   [############--------] 60%
Federation readiness[##------------------] 10%
Mission DoD         [################----] 78%
```

## State path

```text
DARK --✓--> GRAY --✓--> PARTIAL --✓--> LIT --✓--> EXECUTABLE
                                                |
                                                +--> A/B/D/E/W COMPATIBILITY PROVEN
                                                |
                                                +--> ENGINEERING PROMOTION WITHHELD
                                                         |
                                                         v
HEPAK / SAT AUTHORITY --> HARVESTED --> FEDERATED --> PERPETUATED
          NOW                 ○             ○              ○
```

## Temporal hook / event ribbon

```text
2026-09-11 11:00  mission seed
       |
       11:41  helium smoke PASS A/B/D/W; 2 K boundary flagged
       |
       14:08  exact-head build + smoke PASS
       |
       14:36  control repair merged
       |
2026-09-12 17:25  W145 exact-source A/B/D/E/W 5/5 PASS
       |
       NOW  measure runtime phases -> split FAST/HEAVY -> classify first true red
```

## Delta strip — since previous accepted gate

```text
+ exact W145 source-head proof                 PASS
+ A/B/D/E/W finite property evaluations       5/5 PASS
+ exact receipt checksum                      BOUND
+ real hosted runner                          runner_id 1000256609
+ latest runtime evidence anchor              BOUND
+ status staleness guard                      IMPLEMENTING W4
+ phase telemetry                             IMPLEMENTING W4
~ engineering / Qeq authority                 WITHHELD
~ HEPAK / SAT authority                       REQUIRED
~ governed local adapter                      MISSING
~ federation consumer                         MISSING
```

## Measured runtime pressure — W145 run 34707993462

GitHub Actions timestamps have one-second resolution, so sub-second numerical execution is represented as `0 s` in step metadata even though the runtime receipt proves real >0-step evaluation.

```text
Checkout exact source head       32 s
Setup Python                      0 s
Install prerequisites             8 s
Build + install CoolProp        176 s   <<< dominant
Execute five-state probe          0 s   <<< <1 s at Actions timestamp resolution
Checksum                          0 s
Artifact upload                   1 s
Job execution                   223 s
Queue                             3 s
```

The first performance hypothesis is therefore **build/setup separation**, not numerical optimization. W4 telemetry must measure repeated runs before freezing PCA loadings.

## Current blocker stack

```text
1 [HIGH]   BG-HEPAK-CROSSCHECK          Scientist + TM
2 [MEDIUM] BG-LOCAL-ADAPTER-MISSING     Engineer
3 [MEDIUM] BG-FEDERATION-CONSUMER       Engineer + QA
```

## Current lane pressure

```text
P0  L6 PERFORMANCE   phase telemetry + FAST/HEAVY boundary
P0  L10 CONTROL      qualified-runtime staleness guard
P1  L3 RUNTIME      reusable exact-source producer / FAST consumer
P1  L2 READER       classify red workflows before repair
P1  L4 REPAIR       pull only first genuine functional red
P2  L5 MODERNIZE    optimize measured stale/high-load surfaces
P2  L9 FEDERATION   consume only qualified exact-SHA evidence
P3  L7/L8            architecture + bounded innovation
```

## Traffic-light gate view

```text
[GREEN] repo illuminated
[GREEN] meaningful runtime >0
[GREEN] exact source SHA assertion
[GREEN] A/B/D/E/W compatibility property probe 5/5
[GREEN] source-bound receipt checksum
[AMBER] runtime build dominates wall time
[AMBER] 2 K / Qeq engineering authority
[AMBER] governed property adapter
[AMBER] separate federation consumer
[GRAY]  repeated FAST consumer proof
[GRAY]  perpetuation / independent consumer repeat
```

## Recursive control rule

Every meaningful pulse MUST:

`read latest accepted event -> reduce state -> derive BG/CG -> allocate lane + role + runtime class -> execute -> verify receipts -> append event -> regenerate/guard derived status -> message home -> recurse`

First-red semantics:

`RED -> Reader anchors -> Doctor classifies -> external/blocker => DEFER/BD; repairable => Engineer smallest patch -> child runtime -> PASS promote / RED recurse`

Do not delete earlier events. Do not rewrite history to make a later result look cleaner. Corrections are new events linked to the event they supersede.
