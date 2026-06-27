# Plan 4 — Phase A Event Catalog (Pre-Registration Artifact)

**Written from public record only. Committed before any Phase B query ran — git history is the
timestamp.**

This is the Phase A pre-registration artifact for Plan 4 (gated DiD natural experiment) — see ADR-0009.

---

## Purpose

All candidate events, hypotheses, and donut state assignments are locked here before any
outcome data is queried. Selection among viable candidates is mechanical: Phase B checks
pre-period cell counts only, never outcomes (gate condition 4(pre)).

---

## Candidate 1 — `truckers_strike_2018`

| Field | Value |
|-------|-------|
| **Description** | Nationwide truckers' strike (*greve dos caminhoneiros*), 2018-05-21 to 2018-05-30: road freight halted; long-haul routes to North/Northeast depend on trucking from Southeast distribution hubs. |
| **Source / Citation** | Widely documented national event; e.g. https://en.wikipedia.org/wiki/2018_Brazil_truck_drivers%27_strike |
| **Boundary date** | 2018-05-21 (post period starts here, inclusive) |
| **Estimation window** | 2018-01-01 to 2018-09-01 (exclusive) |
| **Primary outcome** | `delivery_days` |
| **Expected sign** | +1 (deliveries slower, more so far from hubs) |

### Hypothesis

Road freight disruption from the strike disproportionately lengthens delivery times in states
that depend on long-haul trucking from Southeast distribution hubs (North and Northeast). States
closer to those hubs (Southeast and South) see a smaller delivery-time increase, creating a
differential treatment effect measurable in a DiD framework.

### Donut State Assignment

| Bloc | State codes |
|------|-------------|
| **Treated** | `AC`, `AM`, `AP`, `PA`, `RO`, `RR`, `TO` *(North)*, `AL`, `BA`, `CE`, `MA`, `PB`, `PE`, `PI`, `RN`, `SE` *(Northeast)* |
| **Control** | `ES`, `MG`, `RJ`, `SP` *(Southeast)*, `PR`, `RS`, `SC` *(South)* |
| **Excluded (middle)** | `DF`, `GO`, `MS`, `MT` *(Center-West)* |

### Viability Verdict

**`viable_on_paper: True`**

Rationale: Externally dated; exposure gradient is geographic (freight distance from SE hubs);
donut drops ambiguous Center-West.

---

## Candidate 2 — `black_friday_2017`

| Field | Value |
|-------|-------|
| **Description** | Black Friday demand spike, 2017-11-24. |
| **Source / Citation** | Annual retail calendar date (public record). |
| **Boundary date** | 2017-11-24 |
| **Estimation window** | 2017-08-01 to 2018-01-01 (exclusive) |
| **Primary outcome** | `log_orders` |
| **Expected sign** | +1 |

### Hypothesis (hypothetical)

Black Friday would generate a national demand spike. No viable geography-only
treated/control contrast exists because exposure is national — every state experiences the
shock. Gate condition 2 (identifying geographic treatment variation) is unsatisfiable.

### Donut State Assignment (as coded, for reference)

| Bloc | State codes |
|------|-------------|
| **Treated** | `AC`, `AM`, `AP`, `PA`, `RO`, `RR`, `TO`, `AL`, `BA`, `CE`, `MA`, `PB`, `PE`, `PI`, `RN`, `SE` |
| **Control** | `ES`, `MG`, `RJ`, `SP`, `PR`, `RS`, `SC` |
| **Excluded** | `DF`, `GO`, `MS`, `MT` |

### Viability Verdict

**`viable_on_paper: False`**

Rationale: NOT viable on paper — exposure is national; no geography-only treated/control
contrast exists (gate condition 2 unsatisfiable). Kept in catalog to document the rejection.

---

## Candidate 3 — `carnival_2018`

| Field | Value |
|-------|-------|
| **Description** | Carnival week, 2018-02-13 (Shrove Tuesday). |
| **Source / Citation** | Brazilian national calendar (public record). |
| **Boundary date** | 2018-02-13 |
| **Estimation window** | 2017-11-01 to 2018-04-01 (exclusive) |
| **Primary outcome** | `log_orders` |
| **Expected sign** | -1 |

### Hypothesis (hypothetical)

Carnival celebrations in major hub cities (RJ, BA, PE, SP) suppress e-commerce orders during
the holiday week relative to states without large public celebrations.

### Donut State Assignment

| Bloc | State codes |
|------|-------------|
| **Treated** | `RJ`, `BA`, `PE`, `SP` *(major public celebrations)* |
| **Control** | `PR`, `RS`, `SC` *(South)*, `MG`, `ES` |
| **Excluded** | `AC`, `AM`, `AP`, `PA`, `RO`, `RR`, `TO` *(North)*, `AL`, `CE`, `MA`, `PB`, `PI`, `RN`, `SE` *(partial Northeast)*, `DF`, `GO`, `MS`, `MT` *(Center-West)* |

### Viability Verdict

**`viable_on_paper: False`**

Rationale: NOT viable on paper — ~1-week transient shock with ambiguous sign and too few
post-boundary weeks of differential exposure for ≥3 lead/lag structure. Kept to document the
rejection.

---

## Selection Rule

The first `viable_on_paper` candidate whose pre-period feasibility (Phase B) passes gate
condition 4(pre) is selected; no outcome data informs selection.

`truckers_strike_2018` is the only on-paper-viable candidate. The other two entries
(`black_friday_2017`, `carnival_2018`) are documented rejections kept to show the reasoning
— they will not be re-evaluated.

---

*Source of truth for state codes and rationale: `src/did/catalog.py` — this document mirrors it
verbatim. If the two ever disagree, `catalog.py` governs.*
