# Frontend Integration Map (AI Hedge Fund)

This map applies the generated design system to the existing frontend stack:

- React + TypeScript + Vite
- Tailwind CSS
- shadcn/radix component layer

## Current Frontend Sources

- CSS variables: `app/frontend/src/index.css`
- Tailwind token bridge: `app/frontend/tailwind.config.ts`
- shadcn primitives: `app/frontend/src/components/ui/*`

## Token Mapping Strategy

Map `tokens/tokens.source.json` semantic tokens into existing CSS custom properties.

Proposed mapping:

- `semantic.surface.page` -> `--background`
- `semantic.surface.panel` -> `--panel-bg`, `--card`
- `semantic.text.primary` -> `--foreground`
- `semantic.text.secondary` -> `--muted-foreground`
- `semantic.border.default` -> `--border`, `--node-border`
- `semantic.action.primary` -> `--primary`, `--tab-accent`
- `semantic.action.accent` -> `--sidebar-ring`
- `semantic.status.gain` -> new `--status-gain`
- `semantic.status.loss` -> new `--status-loss`
- `semantic.status.warn` -> new `--status-warn`

## Component Adoption Order

1. `Button`, `Card`, `Badge`
2. `Tabs`, `Dialog`, `Sidebar`
3. Flow-specific components (`FlowNode`, `OutputPanel`, status indicators)

## Safe Rollout Plan

1. Introduce token variables in `index.css` alongside existing variables.
2. Wire Tailwind color aliases to new variables in `tailwind.config.ts`.
3. Update shared shadcn wrappers first (`button.tsx`, `card.tsx`, `tabs.tsx`).
4. Apply flow/node panel components after shared primitives are stable.
5. Add visual regression snapshots for light/dark modes.

## Accessibility Requirements

- Enforce visible focus on all keyboard-operable controls.
- Validate contrast for primary actions and status text in both themes.
- Preserve tab order and ARIA semantics for dialog/tabs/sidebar interactions.

## Non-Goals

- No changes to trading logic, API flows, or backtesting engines.
- No dependency on project-specific backend data models.
