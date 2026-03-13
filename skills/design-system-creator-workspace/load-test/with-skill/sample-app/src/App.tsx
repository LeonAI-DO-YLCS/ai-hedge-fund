import { Button } from './components/Button';
import { Card } from './components/Card';

export default function App() {
  return (
    <main className="min-h-screen bg-[var(--color-surface-page)] text-[var(--color-text-primary)] p-8"> 
      <section className="mx-auto max-w-4xl space-y-6">
        <header className="space-y-2">
          <h1 className="text-3xl font-semibold">Design System Showcase</h1>
          <p className="text-[var(--color-text-secondary)]">
            Framework-neutral tokens with React adapter demonstration.
          </p>
        </header>
        <div className="grid gap-4 md:grid-cols-2">
          <Card title="Primary Action">
            <Button>Continue</Button>
          </Card>
          <Card title="Surface and Border Tokens">
            <p className="text-sm text-[var(--color-text-secondary)]">
              Panel, border, and typography all map to semantic tokens.
            </p>
          </Card>
        </div>
      </section>
    </main>
  );
}
