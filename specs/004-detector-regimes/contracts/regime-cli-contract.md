# Regime CLI Contract

## Purpose

Define how the existing detector CLI should expose the regime layer without creating a separate runtime tool.

## Command Behavior

The regime layer extends existing detector workflows rather than introducing a separate standalone command family.

### `rid analyze`

**Required regime behavior**:
- Must execute regime classification when the configured analysis groups include the regime layer
- Must emit regime-aware sections in run artifacts
- Must surface regime warnings when coverage is sparse, dominant, missing, or invalid

### `rid inspect-run`

**Required regime behavior**:
- Must expose the stored regime summary and regime-warning context for a completed run

### `rid validate`

**Required regime behavior**:
- Does not need to perform full regime classification, but must preserve compatibility with later regime-enabled analysis runs

## Configuration Interaction

- The detector must support regime-layer settings through detector-local configuration.
- A completed run must record which regime configuration was used.
- Invalid regime configuration must fail clearly rather than silently producing misleading output.

## Scope Rules

- The regime layer remains part of the detector-local CLI only.
- No main-project CLI, backend, or frontend contracts are changed by this feature.
