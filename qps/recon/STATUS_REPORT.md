# QPS DARKLAND RECON — Temporal Status Report

This file is a **derived human view** of `TEMPORAL_STATUS_HOOK.yaml`. The canonical mission table remains authoritative; dashboard elements are compact projections only.

## Canonical mission table

| Mission | Wave | Pulse | State | BG | CG | Crew | DoD | DoV | Next decision |
|---|---|---|---|---|---|---|---:|---:|---|
| M01 CoolProp | CONTROL → SCIENCE | P3 exact-head accepted | EXECUTABLE / A-B-D-W PROVEN | HEPAK cross-check; local adapter; separate consumer | HEPAK comparison → adapter → QPS consumer | PM, TM, Analyst, Scientist, Engineer, QA | 76% | 0/3 | STAY + RECONFIGURE |

## Status ribbon

`M01  EXECUTABLE  | RUNTIME 100 | EVIDENCE 80 | TECH 76 | HARVEST 55 | FEDERATE 10 | DoD 76 | DoV 0/3`

## Compact bars

```text
Visibility          [###################-] 95%
Runtime proof       [####################] 100%
Evidence            [################----] 80%
Technical confidence[###############-----] 76%
Repair closure      [####################] 100%
Harvest readiness   [###########---------] 55%
Federation readiness[##------------------] 10%
Mission DoD         [###############-----] 76%
```

## State path

```text
DARK --✓--> GRAY --✓--> PARTIAL --✓--> LIT --✓--> EXECUTABLE
                                                |
                                                +--> A/B/D/W PROVEN
                                                |
                                                +--> 2 K VALIDATION_REQUIRED
                                                         |
                                                         v
HEPAK CROSSCHECK --> HARVESTED --> FEDERATED --> PERPETUATED
       NOW              ○             ○              ○
```

## Temporal hook / event ribbon

```text
11:00  mission seed
  |
11:41  helium smoke PASS A/B/D/W; 2 K boundary flagged
  |
12:45  PR #1 recon merged
  |
14:05  PR #3 control repair opened
  |
14:08  exact-head assertion + build + smoke PASS
  |
14:36  PR #3 merged
  |
  NOW  BG = HEPAK cross-check -> governed adapter -> separate QPS consumer
```

## Delta strip — since previous accepted gate

```text
+ exact source-head proof        PASS
+ real runner                    runner_id 1000245110
+ A/B/D/W runtime                PASS
+ BG-RUNTIME-UNKNOWN             RETIRED
+ BG-SHA-BINDING-MISMATCH        RETIRED
~ 2 K authority                  HOLD / HEPAK cross-check
~ governed local adapter         MISSING
~ federation consumer            MISSING
crew                             RECON -> SCIENCE/ENGINEERING/QA
```

## Current blocker stack

```text
1 [HIGH]   BG-HEPAK-CROSSCHECK          Scientist + TM
2 [MEDIUM] BG-LOCAL-ADAPTER-MISSING     Engineer
3 [MEDIUM] BG-FEDERATION-CONSUMER       Engineer + QA
```

## Crew strip

```text
ACTIVE   PM | TM | Analyst | Scientist | Engineer | QA
RESERVE  Dockmaster | Doctor | Ambassador | Governor
RETURNED Scout-1 | Scout-2 | Scout-3 | Reader-1 | Reader-2
```

## Traffic-light gate view

```text
[GREEN] repo illuminated
[GREEN] meaningful runtime >0
[GREEN] exact source SHA assertion
[GREEN] A/B/D/W property probe
[AMBER] 2 K scientific authority
[AMBER] governed property adapter
[AMBER] separate QPS consumer
[GRAY]  perpetuation / fresh independent consumer repeat
```

## Recursive update rule

Every meaningful pulse MUST:

`read latest accepted event -> reduce state -> derive BG/CG -> reallocate crew -> execute -> verify receipts -> append event -> refresh canonical table -> refresh compact projections -> message home -> recurse`

Do not delete earlier events. Do not rewrite history to make a later result look cleaner. Corrections are new events linked to the event they supersede.
