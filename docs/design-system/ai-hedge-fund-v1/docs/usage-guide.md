# Usage Guide

## Adoption Steps

1. Import token variables into the target renderer.
2. Build primitives with semantic tokens only.
3. Compose product components from primitives.
4. Validate interaction and accessibility behavior.

## Implementation Notes

- Keep token aliases stable.
- Avoid direct primitive usage in feature-level components.
- Keep component APIs aligned with state model documented in specs.

## Contribution Workflow

1. Propose token/component change.
2. Update specs and a11y matrix.
3. Regenerate sample app showcase.
4. Re-run evaluation suite.
