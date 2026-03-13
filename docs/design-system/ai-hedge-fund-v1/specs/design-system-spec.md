# Design System Spec

## Objective

Provide a reusable, project-agnostic design system for the `fintech` domain with a `precision-industrial` tone.

## Foundation Principles

- Keep tokens layered: primitive -> semantic -> component.
- Prefer semantic token usage in UI code.
- Separate design decisions from renderer implementation details.
- Keep naming stable and avoid product-specific identifiers.

## Token Architecture

- Primitive tokens define raw values.
- Semantic tokens map intent.
- Component tokens map UI parts to semantic intent.

## Theming Strategy

- Base mode: light.
- Extend with dark/high-contrast modes without changing component APIs.

## Versioning Rules

- Breaking token rename: major.
- Additive token/component updates: minor.
- Value tweaks with no API impact: patch.
