import type { ReactNode } from 'react';

interface MetricCardProps {
  label: string;
  value: ReactNode;
  hint?: string;
}

export default function MetricCard({ label, value, hint }: MetricCardProps) {
  return (
    <div className="rounded-[2rem] border border-surface-container bg-white p-6 shadow-sm">
      <p className="text-[10px] font-black uppercase tracking-[0.2em] text-outline">{label}</p>
      <div className="mt-4 text-3xl font-black tracking-tight text-primary">{value}</div>
      {hint ? <p className="mt-2 text-sm font-medium text-on-surface-variant">{hint}</p> : null}
    </div>
  );
}
