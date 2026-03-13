import type { ReactNode } from 'react';

type ButtonProps = {
  children: ReactNode;
};

export function Button({ children }: ButtonProps) {
  return (
    <button
      className="rounded-[var(--radius-button)] bg-[var(--color-action-primary)] px-4 py-2 font-medium text-white hover:bg-[var(--color-action-primary-hover)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-action-primary)]"
      type="button"
    >
      {children}
    </button>
  );
}
