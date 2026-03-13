# Implementation Plan: Detector Regime Layer

**Branch**: `004-detector-regimes` | **Date**: 2026-03-13 | **Spec**: `/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/specs/004-detector-regimes/spec.md`
**Input**: Feature specification from `/specs/004-detector-regimes/spec.md`

## Summary

Implement the next detector phase by adding a deterministic regime-classification layer to the external V75 detector, extending existing detector-local outputs with regime-aware summaries and warnings, while preserving reproducibility, detector-local scope, and compatibility with the current reporting and run-artifact workflow.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: pandas, numpy, scipy, statsmodels, arch, matplotlib, PyYAML, rich, pytest  
**Storage**: File-based detector-local outputs only; read-only external CSV input, detector-local manifests, JSON metrics, JSON findings, Markdown reports, optional sidecar artifact files for bar-level regime observations  
**Testing**: pytest with deterministic synthetic fixtures, frozen real-data slices, leak-prevention checks, reproducibility checks, and artifact consistency tests  
**Target Platform**: Local Linux/WSL2 workstation running the standalone detector under `Randomness and Inefficiencies Detector/`  
**Project Type**: Standalone CLI analytics tool extension  
**Performance Goals**: Regime classification remains practical on the full V75 dataset, repeated runs with identical inputs produce identical regime outputs, and reviewers can identify regime prevalence and warnings from the report in under 5 minutes  
**Constraints**: All implementation stays inside `Randomness and Inefficiencies Detector/`; regime labels must be deterministic, leak-free, and based on trailing data only; outputs must remain compatible with existing detector artifacts; no main-project runtime changes; no GPU requirement  
**Scale/Scope**: One primary V75 M1 dataset with 3,782,647 rows, existing detector CLI/report pipeline, multi-axis regime dimensions, detector-local machine-readable and human-readable regime summaries

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Multi-Agent Orchestration**: Pass by non-applicability. This feature extends the standalone detector and does not alter the main project’s multi-agent trading decision system.
- **II. Trading Modes & Execution Safety**: Pass. The regime layer is offline, detector-local, and does not change execution modes or order safety.
- **III. Data-Driven Valuation**: Pass. The regime layer improves traceable market-state analysis and keeps labels reproducible and explainable.
- **IV. Risk-Managed Decision Making**: Pass by isolation. The feature supports future research but does not bypass or modify the main risk workflow.
- **V. Execution & Connection Frameworks**: Pass. No broker, exchange, or connection adapter changes are introduced.
- **VI. MT5 Connection Framework**: Pass by non-applicability. This phase uses historical detector inputs only and does not alter MT5 connectivity.
- **Feature Scope Gate**: Pass. The implementation remains inside `Randomness and Inefficiencies Detector/` plus Speckit planning artifacts.

**Post-Design Re-check**: Pass. The planned regime layer remains detector-local, additive to the existing external tool, and does not require main-project architecture changes.

## Project Structure

### Documentation (this feature)

```text
specs/004-detector-regimes/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── regime-output-contract.md
│   └── regime-cli-contract.md
└── tasks.md
```

### Source Code (repository root)

```text
Randomness and Inefficiencies Detector/
├── config/
│   ├── default.yaml
│   └── local.example.yaml
├── docs/
│   ├── methodology.md
│   └── planning/
├── src/
│   └── rid/
│       ├── cli.py
│       ├── reporting.py
│       ├── validation.py
│       ├── data_audit.py
│       ├── eda.py
│       ├── run_manifest.py
│       ├── progress.py
│       ├── stats_helpers.py
│       └── regimes.py              # new regime-classification module
├── tests/
│   ├── fixtures/
│   ├── test_cli_smoke.py
│   ├── test_reporting.py
│   ├── test_validation.py
│   └── test_regimes.py             # new regime-layer test suite
├── reports/
│   └── runs/
├── artifacts/
│   └── cache/
└── logs/
```

**Structure Decision**: Extend the existing detector CLI and report pipeline with a new detector-local `regimes.py` module, additional config/reporting updates, and dedicated regime tests while keeping all implementation inside `Randomness and Inefficiencies Detector/`.

## Complexity Tracking

No constitution violations require justification.
