interface StatusBadgeProps {
  label: string;
}

const statusClasses: Record<string, string> = {
  available: 'bg-secondary/10 text-secondary border-secondary/20',
  charging: 'bg-secondary text-white border-secondary',
  preparing: 'bg-amber-100 text-amber-800 border-amber-200',
  finishing: 'bg-sky-100 text-sky-800 border-sky-200',
  unavailable: 'bg-slate-200 text-slate-700 border-slate-300',
  faulted: 'bg-error/10 text-error border-error/20',
  accepted: 'bg-secondary/10 text-secondary border-secondary/20',
  unlocked: 'bg-secondary/10 text-secondary border-secondary/20',
  stopped: 'bg-slate-200 text-slate-700 border-slate-300',
};

export default function StatusBadge({ label }: StatusBadgeProps) {
  const normalized = label.trim().toLowerCase();
  const className = statusClasses[normalized] ?? 'bg-surface-container text-primary border-surface-container-high';

  return (
    <span className={`inline-flex items-center rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-wider ${className}`}>
      {label}
    </span>
  );
}
