---
name: design-system-creator
description: Build project-agnostic design systems and produce a complete implementation pack. Use when asked to create or refine a design system, design tokens, component specs, governance docs, accessibility criteria, or a self-contained sample page/app that demonstrates the system. Supports domain-driven system creation without coupling to any specific repository, product codebase, or framework internals.
license: Complete terms in LICENSE.txt
---

# Design System Creator

Create universal design systems that can be applied to any project.

## Core Rules

- Keep outputs project-agnostic by default.
- Do not assume an existing codebase, naming convention, or brand framework unless explicitly provided.
- Keep the design-system core framework-neutral.
- Treat renderer implementations as adapters.
- Always generate the complete output pack unless the user asks for a reduced scope.

## Output Contract

Always produce these artifacts:

1. Token model/spec.
2. Component behavior specs.
3. Usage and governance docs.
4. Accessibility conformance matrix.
5. Self-contained sample implementation package.

Default adapter for sample implementation:

- React + TypeScript + Tailwind in a buildable folder.

## Workflow

1. Capture intent
- Identify domain, audience, tone, and constraints.
- If missing, pick neutral defaults and record assumptions.

2. Build system foundations
- Define principles and naming strategy.
- Define token layers: primitive, semantic, component.
- Define scale systems: spacing, radius, elevation, typography.

3. Define component behavior
- Specify anatomy, states, variants, interactions, and content rules.
- Include keyboard and accessibility behavior for interactive components.

4. Produce docs and governance
- Generate usage guidance and contribution rules.
- Include versioning and change governance guidance.

5. Generate sample implementation package
- Emit a runnable adapter project that consumes semantic tokens.
- Include a showcase page for foundations and key components.

6. Validate completeness
- Ensure all required artifacts are present and internally consistent.

## Progressive Loading

Load only what is needed:

- For schemas and file contracts, read `references/schemas.md`.
- For deterministic artifact scaffolding, run `scripts/generate_design_system_pack.py`.
- For skill quality measurement, use `scripts/run_eval.py` and `scripts/aggregate_benchmark.py`.
- For iterative trigger improvements, use `scripts/run_loop.py` and `scripts/improve_description.py`.

## Evaluation Lifecycle

Use this loop when hardening the skill:

1. Run evals on current skill behavior.
2. Compare with-skill versus without-skill baseline.
3. Aggregate benchmark.
4. Generate review packet and collect feedback.
5. Iterate skill description or behavior.
6. Re-run until stable.

## Quality Gates

Before packaging:

- Trigger quality is acceptable on positives and negatives.
- All required artifacts are generated for positive cases.
- Sample package demonstrates token consumption.
- Accessibility matrix exists and is not empty.

## Notes

- If a user asks for framework-specific details, preserve framework-neutral core artifacts and add framework-specific outputs as adapters.
- If requested output would become project-coupled, explicitly separate reusable core from project-specific extension.
