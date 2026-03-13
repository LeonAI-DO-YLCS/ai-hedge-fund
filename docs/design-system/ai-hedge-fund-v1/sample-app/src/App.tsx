import { Button } from './components/Button';
import { Card } from './components/Card';

export default function App() {
  return (
    <main className="terminal-bg min-h-screen bg-[var(--color-surface-page)] text-[var(--color-text-primary)] p-8">
      <section className="mx-auto max-w-6xl space-y-8">
        <header className="space-y-4">
          <div className="flex items-center justify-between rounded-xl border border-[var(--color-border-default)] bg-[var(--color-surface-panel)] px-4 py-3">
            <p className="tracking-[0.18em] text-xs uppercase text-[var(--color-action-accent)]">
              Live Design System Control Surface
            </p>
            <p className="text-xs text-[var(--color-text-secondary)]">Latency Budget: 42ms</p>
          </div>
          <p className="tracking-[0.2em] text-xs uppercase text-[var(--color-action-primary)]">
            AI Hedge Fund Design System
          </p>
          <h1 className="max-w-4xl text-5xl font-semibold leading-tight">
            Dark-Mode Trading Interface With Institutional Clarity
          </h1>
          <p className="max-w-3xl text-[var(--color-text-secondary)]">
            Purpose-built for graph execution, portfolio controls, and output diagnostics. No decorative noise, only
            readable hierarchy, action confidence, and fast status interpretation.
          </p>
        </header>

        <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
          <Card title="Execution Overview">
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-lg border border-[var(--color-border-default)] bg-[rgb(255_255_255_/_0.02)] p-3">
                <p className="text-xs uppercase text-[var(--color-text-secondary)]">Active Flows</p>
                <p className="mt-2 text-2xl font-semibold">12</p>
              </div>
              <div className="rounded-lg border border-[var(--color-border-default)] bg-[rgb(255_255_255_/_0.02)] p-3">
                <p className="text-xs uppercase text-[var(--color-text-secondary)]">Win Rate</p>
                <p className="mt-2 text-2xl font-semibold text-[var(--color-status-gain)]">68.4%</p>
              </div>
              <div className="rounded-lg border border-[var(--color-border-default)] bg-[rgb(255_255_255_/_0.02)] p-3">
                <p className="text-xs uppercase text-[var(--color-text-secondary)]">Drawdown</p>
                <p className="mt-2 text-2xl font-semibold text-[var(--color-status-loss)]">-4.9%</p>
              </div>
            </div>
          </Card>

          <Card title="Primary Actions">
            <div className="flex flex-wrap gap-3">
              <Button>Run Backtest</Button>
              <Button>Publish Flow</Button>
            </div>
          </Card>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <Card title="Signal Status">
            <div className="space-y-2 text-sm">
              <p className="text-[var(--color-status-gain)]">Gain Signals: +14.2%</p>
              <p className="text-[var(--color-status-loss)]">Loss Signals: -3.1%</p>
              <p className="text-[var(--color-status-warn)]">Warnings: 2 open constraints</p>
            </div>
          </Card>
          <Card title="System Intent">
            <p className="text-sm text-[var(--color-text-secondary)]">
              Semantic tokens define every critical state: command actions, risk markers, and signal confidence.
            </p>
          </Card>
          <Card title="Alert Channel">
            <p className="text-sm text-[var(--color-text-secondary)]">
              3 model drifts detected. Next retrain window in 2h 14m.
            </p>
          </Card>
        </div>

        <Card title="Token Preview">
          <div className="grid gap-3 md:grid-cols-4">
            <div className="rounded-md border border-[var(--color-border-default)] p-3">
              <p className="text-xs uppercase text-[var(--color-text-secondary)]">Primary</p>
              <p className="mt-2 font-mono text-sm text-[var(--color-action-primary)]">#0B5FFF</p>
            </div>
            <div className="rounded-md border border-[var(--color-border-default)] p-3">
              <p className="text-xs uppercase text-[var(--color-text-secondary)]">Accent</p>
              <p className="mt-2 font-mono text-sm text-[var(--color-action-accent)]">#00B8D9</p>
            </div>
            <div className="rounded-md border border-[var(--color-border-default)] p-3">
              <p className="text-xs uppercase text-[var(--color-text-secondary)]">Gain</p>
              <p className="mt-2 font-mono text-sm text-[var(--color-status-gain)]">#11A36A</p>
            </div>
            <div className="rounded-md border border-[var(--color-border-default)] p-3">
              <p className="text-xs uppercase text-[var(--color-text-secondary)]">Loss</p>
              <p className="mt-2 font-mono text-sm text-[var(--color-status-loss)]">#D9485F</p>
            </div>
          </div>
        </Card>
      </section>
    </main>
  );
}
