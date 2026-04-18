import Link from 'next/link';

export default function Sidebar() {
  return (
    <aside className="hidden md:flex fixed left-0 top-0 h-screen w-64 flex-col overflow-y-auto bg-slate-900 p-4">
      <div className="mb-8 flex items-center gap-3 px-4">
        <span className="material-symbols-outlined text-2xl text-secondary" style={{ fontVariationSettings: "'FILL' 1" }}>
          ev_charger
        </span>
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-white">VoltMetric Pro</h1>
          <p className="text-[10px] uppercase tracking-widest text-on-primary-container">Infrastructure MGMT</p>
        </div>
      </div>
      <nav className="flex-1 space-y-1">
        <Link className="flex items-center gap-3 rounded-lg px-4 py-3 text-slate-400 transition-colors hover:bg-slate-800 hover:text-white" href="/dashboard">
          <span className="material-symbols-outlined">dashboard</span>
          <span className="font-headline text-sm font-medium">Dashboard</span>
        </Link>
        <Link className="flex items-center gap-3 rounded-lg px-4 py-3 text-slate-400 transition-colors hover:bg-slate-800 hover:text-white" href="/sites">
          <span className="material-symbols-outlined">location_on</span>
          <span className="font-headline text-sm font-medium">Chargers</span>
        </Link>
        <Link className="flex items-center gap-3 rounded-lg px-4 py-3 text-emerald-400 transition-colors hover:bg-slate-800 hover:text-white" href="/sessions">
          <span className="material-symbols-outlined">receipt_long</span>
          <span className="font-headline text-sm font-medium">Sessions</span>
        </Link>
      </nav>
    </aside>
  );
}
