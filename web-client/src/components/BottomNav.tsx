"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function BottomNav() {
  const pathname = usePathname();

  const links = [
    { href: '/dashboard', icon: 'dashboard', label: 'Dash' },
    { href: '/sites', icon: 'location_on', label: 'Chargers' },
    { href: '/sessions', icon: 'receipt_long', label: 'Sessions' },
  ];

  return (
    <nav className="fixed bottom-0 left-0 z-50 flex h-[72px] w-full items-center justify-around rounded-t-2xl border-t border-slate-800 bg-slate-900 pb-safe md:hidden">
      {links.map((link) => {
        const isActive = pathname.startsWith(link.href);
        return (
          <Link
            key={link.href}
            href={link.href}
            className={`flex flex-col items-center justify-center gap-1 w-20 h-full ${
              isActive ? 'text-secondary' : 'text-slate-400 hover:text-white'
            }`}
          >
            <span
              className="material-symbols-outlined text-2xl mt-1"
              style={isActive ? { fontVariationSettings: "'FILL' 1" } : {}}
            >
              {link.icon}
            </span>
            <span className="text-[10px] font-medium tracking-wide">{link.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
