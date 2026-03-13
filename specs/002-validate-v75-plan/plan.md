# Implementation Plan: Validated V75 Detector Research Plan

**Branch**: `002-validate-v75-plan` | **Date**: 2026-03-12 | **Spec**: `/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/ai-hedge-fund/specs/002-validate-v75-plan/spec.md`
**Input**: Feature specification from `/specs/002-validate-v75-plan/spec.md`

## Summary

Build a standalone external research CLI under `Randomness and Inefficiencies Detector/` that audits the V75 minute dataset, runs low-complexity directional and volatility diagnostics, applies cost-aware and stability-aware validation, and emits decision-grade reports without modifying the main project codebase.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: pandas, numpy, scipy, statsmodels, arch, matplotlib, PyYAML, pytest  
**Storage**: File-based inputs and outputs only; read-only external CSV input, local run manifests, JSON metrics, Markdown reports, plots, and logs  
**Testing**: pytest smoke tests, fixture-based data validation tests, and deterministic report-generation checks  
**Target Platform**: Local Linux/WSL2 research workstation, offline-first execution  
**Project Type**: Standalone CLI analytics tool  
**Performance Goals**: Validate dataset structure in under 5 minutes and complete a full end-to-end analysis run on the current V75 dataset in under 30 minutes on a standard developer workstation  
**Constraints**: All implementation changes must stay inside `Randomness and Inefficiencies Detector/`; no network dependency during normal runs; no changes to `src/`, `app/`, `mt5-connection-bridge/`, or existing test/runtime contracts; all findings must be reproducible from a saved run manifest  
**Scale/Scope**: One primary V75 M1 dataset at `/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/Datasets/Volatility 75 Index_M1_201901010502_202603122158.csv` with 3,782,647 rows spanning 2019-01-01 to 2026-03-12, including variable spread values and minor timestamp gaps

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Multi-Agent Orchestration**: Pass by non-applicability. This feature is a standalone external research tool and does not alter the main trading decision system.
- **II. Trading Modes & Execution Safety**: Pass. The detector is offline-only, emits research conclusions, and does not place orders or alter execution modes.
- **III. Data-Driven Valuation**: Pass. The design prioritizes dataset integrity, traceable evidence, and explicit limits on unsupported claims.
- **IV. Risk-Managed Decision Making**: Pass by isolation. The tool does not bypass or modify the main project risk workflow because it does not integrate into live decision paths.
- **V. Execution & Connection Frameworks**: Pass. No broker, bridge, or execution adapter is modified; main project connectivity remains untouched.
- **VI. MT5 Connection Framework**: Pass. The tool uses historical file inputs only and introduces no MT5 runtime coupling.
- **Feature Scope Gate**: Pass. Planned implementation is confined to `Randomness and Inefficiencies Detector/`, with only Speckit planning artifacts outside that folder.

**Post-Design Re-check**: Pass. Phase 1 artifacts keep the detector isolated, file-based, offline-first, and non-invasive to the main project architecture.

## Project Structure

### Documentation (this feature)

```text
specs/002-validate-v75-plan/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cli-contract.md
│   └── artifact-contract.md
└── tasks.md
```

### Source Code (repository root)

```text
Randomness and Inefficiencies Detector/
├── README.md
├── pyproject.toml
├── .gitignore
├── config/
│   ├── default.yaml
│   └── local.example.yaml
├── docs/
│   └── methodology.md
├── src/
│   └── rid/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── dataset.py
│       ├── data_audit.py
│       ├── directional_tests.py
│       ├── volatility_tests.py
│       ├── tradability.py
│       ├── validation.py
│       ├── reporting.py
│       └── run_manifest.py
├── tests/
│   ├── fixtures/
│   ├── test_data_audit.py
│   ├── test_cli_smoke.py
│   └── test_reporting.py
├── reports/
│   └── runs/
├── artifacts/
│   └── cache/
└── logs/

/home/lnx-ubuntu-wsl/LeonAI_DO/dev/TRADING/Datasets/
└── Volatility 75 Index_M1_201901010502_202603122158.csv
```

**Structure Decision**: Use a self-contained mini-project inside `Randomness and Inefficiencies Detector/` with its own runtime, config, tests, and outputs. Treat the V75 CSV as a read-only external dataset and keep all detector artifacts inside the detector folder.

## Complexity Tracking

No constitution violations require justification.
