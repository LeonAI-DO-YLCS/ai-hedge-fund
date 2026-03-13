#!/usr/bin/env python3
"""Generate a project-agnostic design-system output pack."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import ensure_dir


DEFAULT_COMPONENTS = ["Button", "Input", "Card", "Modal", "Tabs", "Badge"]


def infer_domain(prompt: str, fallback: str) -> str:
    lowered = prompt.lower()
    for candidate in ["fintech", "healthcare", "ecommerce", "saas", "education", "logistics"]:
        if candidate in lowered:
            return candidate
    return fallback


def build_tokens(domain: str) -> dict:
    return {
        "$schema": "https://www.designtokens.org/TR/2025.10/format/",
        "primitive": {
            "color": {
                "neutral": {
                    "0": {"$value": "#FFFFFF", "$type": "color"},
                    "100": {"$value": "#F4F6F8", "$type": "color"},
                    "300": {"$value": "#D0D7DE", "$type": "color"},
                    "700": {"$value": "#1F2937", "$type": "color"},
                    "900": {"$value": "#0B1220", "$type": "color"},
                },
                "brand": {
                    "500": {"$value": "#0F766E", "$type": "color"},
                    "600": {"$value": "#0A5E59", "$type": "color"},
                },
            },
            "spacing": {
                "1": {"$value": "4px", "$type": "dimension"},
                "2": {"$value": "8px", "$type": "dimension"},
                "3": {"$value": "12px", "$type": "dimension"},
                "4": {"$value": "16px", "$type": "dimension"},
                "6": {"$value": "24px", "$type": "dimension"},
                "8": {"$value": "32px", "$type": "dimension"},
            },
            "radius": {
                "sm": {"$value": "6px", "$type": "dimension"},
                "md": {"$value": "10px", "$type": "dimension"},
                "lg": {"$value": "14px", "$type": "dimension"},
            },
        },
        "semantic": {
            "surface": {
                "page": {"$value": "{primitive.color.neutral.100}", "$type": "color"},
                "panel": {"$value": "{primitive.color.neutral.0}", "$type": "color"},
            },
            "text": {
                "primary": {"$value": "{primitive.color.neutral.900}", "$type": "color"},
                "secondary": {"$value": "{primitive.color.neutral.700}", "$type": "color"},
            },
            "border": {
                "default": {"$value": "{primitive.color.neutral.300}", "$type": "color"}
            },
            "action": {
                "primary": {"$value": "{primitive.color.brand.500}", "$type": "color"},
                "primaryHover": {"$value": "{primitive.color.brand.600}", "$type": "color"},
            },
        },
        "component": {
            "button": {
                "bg": {"$value": "{semantic.action.primary}", "$type": "color"},
                "bgHover": {"$value": "{semantic.action.primaryHover}", "$type": "color"},
                "text": {"$value": "{primitive.color.neutral.0}", "$type": "color"},
                "radius": {"$value": "{primitive.radius.md}", "$type": "dimension"},
                "paddingY": {"$value": "{primitive.spacing.2}", "$type": "dimension"},
                "paddingX": {"$value": "{primitive.spacing.4}", "$type": "dimension"},
            },
            "card": {
                "bg": {"$value": "{semantic.surface.panel}", "$type": "color"},
                "border": {"$value": "{semantic.border.default}", "$type": "color"},
                "radius": {"$value": "{primitive.radius.lg}", "$type": "dimension"},
                "padding": {"$value": "{primitive.spacing.6}", "$type": "dimension"},
            },
        },
        "meta": {
            "domain": domain,
            "notes": "Project-agnostic token baseline with semantic-first consumption",
        },
    }


def write_docs(output_dir: Path, domain: str, tone: str, components: list[str]) -> None:
    specs_dir = ensure_dir(output_dir / "specs")
    docs_dir = ensure_dir(output_dir / "docs")

    design_system_spec = f"""# Design System Spec

## Objective

Provide a reusable, project-agnostic design system for the `{domain}` domain with a `{tone}` tone.

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
"""

    component_specs = "# Component Specs\n\n"
    component_specs += "## Coverage\n\n"
    for component in components:
        component_specs += f"- {component}\n"
    component_specs += "\n## Component Behavior\n\n"
    for component in components:
        component_specs += f"### {component}\n"
        component_specs += "- Anatomy: root, content, optional icon/label slot.\n"
        component_specs += "- States: default, hover, focus-visible, disabled, loading.\n"
        component_specs += "- Accessibility: keyboard reachable, visible focus, semantic role when interactive.\n"
        component_specs += "- Content rules: concise labels, avoid truncation for critical actions.\n\n"

    usage_guide = """# Usage Guide

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
"""

    governance = """# Governance

## Decision Model

- Design system council approves breaking changes.
- Product teams can add local wrappers without mutating core tokens.

## Change Control

- Every change must include rationale and migration notes.
- Every interactive component change must include accessibility review.

## Deprecation Policy

- Mark deprecated tokens/components for at least one minor release before removal.
"""

    a11y = """# Accessibility Conformance Matrix

| Area | Requirement | Status | Notes |
|---|---|---|---|
| Color contrast | WCAG 2.2 contrast ratios | Planned | Validate at implementation time |
| Keyboard nav | All interactive controls keyboard operable | Planned | Include tab order and focus-visible |
| Focus indicator | Visible focus for keyboard interactions | Planned | Use semantic focus tokens |
| Target size | Interactive controls sized for usability | Planned | Enforce in component specs |
| ARIA patterns | APG-aligned behavior for composite widgets | Planned | Tabs, dialog, menu patterns |
"""

    (specs_dir / "design-system-spec.md").write_text(design_system_spec, encoding="utf-8")
    (specs_dir / "component-specs.md").write_text(component_specs, encoding="utf-8")
    (docs_dir / "usage-guide.md").write_text(usage_guide, encoding="utf-8")
    (docs_dir / "governance.md").write_text(governance, encoding="utf-8")
    (docs_dir / "a11y-conformance-matrix.md").write_text(a11y, encoding="utf-8")


def write_sample_app(output_dir: Path) -> None:
    app_dir = ensure_dir(output_dir / "sample-app")
    src_dir = ensure_dir(app_dir / "src")
    component_dir = ensure_dir(src_dir / "components")

    package_json = {
        "name": "design-system-sample-app",
        "private": True,
        "version": "0.1.0",
        "type": "module",
        "scripts": {
            "dev": "vite",
            "build": "tsc -b && vite build",
            "preview": "vite preview",
        },
        "dependencies": {
            "react": "^18.3.1",
            "react-dom": "^18.3.1",
        },
        "devDependencies": {
            "@types/react": "^18.3.12",
            "@types/react-dom": "^18.3.1",
            "@vitejs/plugin-react": "^4.3.3",
            "autoprefixer": "^10.4.20",
            "postcss": "^8.4.47",
            "tailwindcss": "^3.4.13",
            "typescript": "^5.6.3",
            "vite": "^5.4.10",
        },
    }

    (app_dir / "package.json").write_text(json.dumps(package_json, indent=2) + "\n", encoding="utf-8")
    (app_dir / "index.html").write_text(
        """<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"UTF-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
    <title>Design System Sample</title>
  </head>
  <body>
    <div id=\"root\"></div>
    <script type=\"module\" src=\"/src/main.tsx\"></script>
  </body>
</html>
""",
        encoding="utf-8",
    )
    (app_dir / "vite.config.ts").write_text(
        """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
});
""",
        encoding="utf-8",
    )
    (app_dir / "postcss.config.js").write_text(
        """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
""",
        encoding="utf-8",
    )
    (app_dir / "tailwind.config.ts").write_text(
        """import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {},
  },
  plugins: [],
};

export default config;
""",
        encoding="utf-8",
    )
    (app_dir / "tsconfig.json").write_text(
        """{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "Bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true
  },
  "include": ["src", "vite.config.ts", "tailwind.config.ts"]
}
""",
        encoding="utf-8",
    )

    (src_dir / "main.tsx").write_text(
        """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
""",
        encoding="utf-8",
    )

    (src_dir / "App.tsx").write_text(
        """import { Button } from './components/Button';
import { Card } from './components/Card';

export default function App() {
  return (
    <main className=\"min-h-screen bg-[var(--color-surface-page)] text-[var(--color-text-primary)] p-8\"> 
      <section className=\"mx-auto max-w-4xl space-y-6\">
        <header className=\"space-y-2\">
          <h1 className=\"text-3xl font-semibold\">Design System Showcase</h1>
          <p className=\"text-[var(--color-text-secondary)]\">
            Framework-neutral tokens with React adapter demonstration.
          </p>
        </header>
        <div className=\"grid gap-4 md:grid-cols-2\">
          <Card title=\"Primary Action\">
            <Button>Continue</Button>
          </Card>
          <Card title=\"Surface and Border Tokens\">
            <p className=\"text-sm text-[var(--color-text-secondary)]\">
              Panel, border, and typography all map to semantic tokens.
            </p>
          </Card>
        </div>
      </section>
    </main>
  );
}
""",
        encoding="utf-8",
    )

    (src_dir / "index.css").write_text(
        """@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --color-surface-page: #f4f6f8;
  --color-surface-panel: #ffffff;
  --color-text-primary: #0b1220;
  --color-text-secondary: #1f2937;
  --color-border-default: #d0d7de;
  --color-action-primary: #0f766e;
  --color-action-primary-hover: #0a5e59;
  --radius-card: 14px;
  --radius-button: 10px;
}

body {
  margin: 0;
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif;
}
""",
        encoding="utf-8",
    )

    (component_dir / "Button.tsx").write_text(
        """import type { ReactNode } from 'react';

type ButtonProps = {
  children: ReactNode;
};

export function Button({ children }: ButtonProps) {
  return (
    <button
      className=\"rounded-[var(--radius-button)] bg-[var(--color-action-primary)] px-4 py-2 font-medium text-white hover:bg-[var(--color-action-primary-hover)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-action-primary)]\"
      type=\"button\"
    >
      {children}
    </button>
  );
}
""",
        encoding="utf-8",
    )

    (component_dir / "Card.tsx").write_text(
        """import type { ReactNode } from 'react';

type CardProps = {
  title: string;
  children: ReactNode;
};

export function Card({ title, children }: CardProps) {
  return (
    <article className=\"rounded-[var(--radius-card)] border border-[var(--color-border-default)] bg-[var(--color-surface-panel)] p-6\">
      <h2 className=\"mb-3 text-lg font-semibold\">{title}</h2>
      {children}
    </article>
  );
}
""",
        encoding="utf-8",
    )


def generate_pack(prompt: str, output_dir: Path, domain: str, tone: str, components: list[str]) -> None:
    ensure_dir(output_dir)
    tokens_dir = ensure_dir(output_dir / "tokens")
    tokens = build_tokens(domain)
    (tokens_dir / "tokens.source.json").write_text(json.dumps(tokens, indent=2) + "\n", encoding="utf-8")

    write_docs(output_dir, domain=domain, tone=tone, components=components)
    write_sample_app(output_dir)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a complete design-system output pack.")
    parser.add_argument("--prompt", required=True, help="User prompt describing requested system")
    parser.add_argument("--output-dir", required=True, help="Output directory for generated artifacts")
    parser.add_argument("--domain", default="general", help="Domain label")
    parser.add_argument("--tone", default="professional", help="Design tone label")
    parser.add_argument("--components", default=",".join(DEFAULT_COMPONENTS), help="Comma-separated component list")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    domain = infer_domain(args.prompt, args.domain)
    components = [c.strip() for c in args.components.split(",") if c.strip()]

    generate_pack(
        prompt=args.prompt,
        output_dir=output_dir,
        domain=domain,
        tone=args.tone,
        components=components or DEFAULT_COMPONENTS,
    )
    print(f"Generated design-system pack at: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
