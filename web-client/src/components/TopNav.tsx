"use client";

import { usePathname } from 'next/navigation';

const PAGE_TITLES: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/sites': 'Chargers',
  '/sessions': 'Sessions',
};

function getPageTitle(pathname: string) {
  if (pathname.startsWith('/sites/')) {
    return 'Charger Detail';
  }
  if (pathname.startsWith('/sessions/')) {
    return 'Session Detail';
  }
  return PAGE_TITLES[pathname] ?? 'EV Operations';
}

export default function TopNav() {
  const pathname = usePathname();

  return (
    <header className="fixed top-0 right-0 z-10 flex h-16 w-[calc(100%-16rem)] items-center justify-between border-b border-slate-100 bg-white/80 px-8 backdrop-blur-md">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-outline">OCPP Live View</p>
        <h2 className="mt-1 text-lg font-bold tracking-tight text-primary">{getPageTitle(pathname)}</h2>
      </div>
      <span className="rounded-full bg-secondary/10 px-3 py-1.5 text-sm font-bold text-secondary">Live data</span>
    </header>
  );
}
