import type { ReactNode } from 'react';

type CardProps = {
  title: string;
  children: ReactNode;
};

export function Card({ title, children }: CardProps) {
  return (
    <article className="rounded-[var(--radius-card)] border border-[var(--color-border-default)] bg-[var(--color-surface-panel)] p-6 shadow-[0_8px_24px_rgb(15_23_42_/_0.08)]">
      <h2 className="mb-3 text-lg font-semibold after:ml-3 after:inline-block after:h-px after:w-10 after:bg-[var(--color-action-accent)] after:align-middle">{title}</h2>
      {children}
    </article>
  );
}
