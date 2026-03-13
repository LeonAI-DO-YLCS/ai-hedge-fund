# Schemas

## 1. Evals Schema (`evals/evals.json`)

```json
{
  "version": "1.0",
  "evals": [
    {
      "id": "string",
      "prompt": "string",
      "expected_trigger": true,
      "required_artifacts": [
        "tokens/tokens.source.json",
        "specs/design-system-spec.md",
        "specs/component-specs.md",
        "docs/usage-guide.md",
        "docs/governance.md",
        "docs/a11y-conformance-matrix.md",
        "sample-app/package.json"
      ]
    }
  ]
}
```

Rules:

- `id` must be unique.
- `expected_trigger` is required for positive and negative trigger checks.
- `required_artifacts` can be empty for negative trigger tests.

## 2. Run Output Layout

Each evaluation run writes into:

- `<workspace>/iteration-<N>/<eval-id>/with_skill/`
- `<workspace>/iteration-<N>/<eval-id>/without_skill/`

Each mode folder includes:

- `responses/run-<k>.json`
- `timing.json`
- `grading.json`

## 3. Response Schema (`responses/run-<k>.json`)

```json
{
  "run_index": 1,
  "mode": "with_skill",
  "triggered": true,
  "artifact_root": "string",
  "missing_artifacts": [],
  "notes": "string"
}
```

## 4. Timing Schema (`timing.json`)

```json
{
  "mode": "with_skill",
  "runs": 3,
  "duration_seconds": {
    "min": 0.0,
    "max": 0.0,
    "avg": 0.0
  }
}
```

## 5. Grading Schema (`grading.json`)

```json
{
  "mode": "with_skill",
  "expected_trigger": true,
  "trigger_rate": 1.0,
  "trigger_pass": true,
  "artifact_pass_rate": 1.0,
  "artifact_pass": true,
  "overall_pass": true,
  "required_artifacts": ["..."],
  "artifact_coverage": {
    "tokens/tokens.source.json": 1.0
  }
}
```

## 6. Benchmark Schema (`benchmark.json`)

```json
{
  "version": "1.0",
  "iteration": 1,
  "summary": {
    "eval_count": 0,
    "with_skill_pass_rate": 0.0,
    "without_skill_pass_rate": 0.0,
    "delta_pass_rate": 0.0,
    "with_skill_trigger_precision": 0.0,
    "with_skill_trigger_recall": 0.0,
    "without_skill_trigger_precision": 0.0,
    "without_skill_trigger_recall": 0.0
  },
  "eval_results": [
    {
      "id": "string",
      "expected_trigger": true,
      "with_skill": {
        "overall_pass": true,
        "trigger_rate": 1.0,
        "artifact_pass_rate": 1.0
      },
      "without_skill": {
        "overall_pass": false,
        "trigger_rate": 0.0,
        "artifact_pass_rate": 0.0
      }
    }
  ]
}
```

## 7. Feedback Schema (`feedback.json`)

```json
{
  "reviewer": "string",
  "date": "YYYY-MM-DD",
  "overall_decision": "accept|iterate|reject",
  "findings": [
    {
      "severity": "low|medium|high",
      "category": "trigger|artifact|a11y|docs|sample-app",
      "message": "string",
      "recommended_action": "string"
    }
  ]
}
```
