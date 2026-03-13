import type { ReactNode } from 'react';

type CardProps = {
  title: string;
  children: ReactNode;
};

export function Card({ title, children }: CardProps) {
  return (
    <article className="rounded-[var(--radius-card)] border border-[var(--color-border-default)] bg-[var(--color-surface-panel)] p-6">
      <h2 className="mb-3 text-lg font-semibold">{title}</h2>
      {children}
    </article>
  );
}
