# Waze Cargo — 2026 Forecast Accuracy Summary

**National totals (Jan–May 2026):**

| | Imports | Exports | Total |
|---|---:|---:|---:|
| Actual | 316,634 | 77,303 | 393,937 |
| Forecast | 341,052 | 80,757 | 421,809 |
| Error | +7.7% | +4.5% | **+7.1%** |

**By port size (wMAPE):**

| Category | Pairs | wMAPE | Best | Worst |
|---|---:|---:|---|---|
| **Large** (>=500/mo) | 11 | **8.3%** | San Antonio export (1.2%) | Valparaiso import (26.1%) |
| **Medium** (50-500/mo) | 10 | **17.1%** | Iquique import (1.2%) | Coquimbo export (127%) |
| **Small** (<50/mo) | 33 | **25.2%** | Chanaral export (0%) | Penco export (500%) |
| **Overall** | 54 | **8.5%** | | |

**Key highlights:**

- **San Antonio import** (57% of all maritime imports): **3.4% error** — excellent
- **San Antonio export**: **1.2% error** — near-perfect
- **Valparaiso import** is the biggest miss: **+26.1%** over-prediction, driven by a +91% miss in May
- The 2025 holdout wMAPE was 4.03%; the live 2026 wMAPE of 8.5% shows expected degradation for a fully out-of-sample recursive forecast
- Large ports carry 98% of volume and have 8.3% wMAPE — the model is most accurate where it matters most
