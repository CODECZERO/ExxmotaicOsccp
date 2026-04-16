"use client";

import Link from 'next/link';
import { useMemo, useState } from 'react';

import MetricCard from '@/components/MetricCard';
import StatusBadge from '@/components/StatusBadge';
import { useActiveSessions, useDashboardStats, useSessions } from '@/hooks/useData';
import { useLiveStream } from '@/hooks/useLiveStream';
import { formatDateTime, formatInteger, formatNumber } from '@/lib/format';

export default function ActiveSession() {
  useLiveStream({
    keys: ['/sessions', '/sessions/active', '/stats'],
  });

  const { sessions, isLoading, isError } = useSessions();
  const { sessions: activeSessions } = useActiveSessions();
  const { stats } = useDashboardStats();
  const [query, setQuery] = useState('');

  const filteredSessions = useMemo(() => {
    const value = query.trim().toLowerCase();
    if (!value) {
      return sessions;
    }

    return sessions.filter((session) =>
      [session.transaction_id, session.charger_id, session.id_tag ?? '']
        .some((item) => item.toLowerCase().includes(value)),
    );
  }, [query, sessions]);

  if (isError) {
    return (
      <div className="flex min-h-screen flex-1 items-center justify-center bg-surface-container-lowest">
        <div className="rounded-[2rem] border border-error/20 bg-white p-8 text-center shadow-xl">
          <span className="material-symbols-outlined text-6xl text-error">warning</span>
          <h2 className="mt-4 text-2xl font-black text-primary">Session feed unavailable</h2>
          <p className="mt-2 text-on-surface-variant">The frontend could not fetch charging sessions from the backend API.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 bg-surface-container-lowest">
      <div className="mx-auto flex max-w-[1600px] flex-col gap-8 px-8 pb-12 pt-28">
        <section className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="mt-3 text-4xl font-black tracking-tight text-primary">Charging session operations</h1>
            <p className="mt-2 max-w-2xl text-sm font-medium text-on-surface-variant">
              Integrated with full session listing, active session view, per-session detail, and remote stop support from the backend.
            </p>
          </div>
        </section>

        <section className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Total Sessions" value={formatInteger(stats?.sessions.total ?? sessions.length)} hint="Unified charging session list" />
          <MetricCard label="Active Sessions" value={formatInteger(activeSessions.length)} hint="Live backend session count" />
          <MetricCard label="Online Chargers" value={formatInteger(stats?.chargers.online ?? 0)} hint="Chargers available to transact" />
          <MetricCard label="Energy Delivered" value={`${formatNumber(stats?.sessions.total_energy_kwh ?? 0)} kWh`} hint="Dashboard aggregate energy" />
        </section>

        <section className="grid grid-cols-1 gap-8 xl:grid-cols-[0.9fr_1.1fr]">
          <div className="rounded-[2.5rem] border border-surface-container bg-white p-8 shadow-sm">
            <h2 className="text-2xl font-black tracking-tight text-primary">Live now</h2>
            <p className="mt-1 text-sm text-on-surface-variant">Using `GET /api/sessions/active`.</p>
            <div className="mt-6 space-y-3">
              {activeSessions.slice(0, 6).map((session) => (
                <Link
                  key={session.id}
                  href={`/sessions/${session.id}`}
                  className="block rounded-[1.75rem] border border-surface-container bg-surface-container-lowest p-5 transition hover:border-secondary"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="font-black text-primary">#{session.transaction_id}</p>
                      <p className="mt-1 text-sm text-on-surface-variant">{session.charger_id} · {session.id_tag || 'Guest / Public'}</p>
                    </div>
                    <StatusBadge label="Charging" />
                  </div>
                  <p className="mt-3 text-xs font-semibold uppercase tracking-[0.2em] text-outline">
                    Started {formatDateTime(session.start_time)}
                  </p>
                </Link>
              ))}
              {activeSessions.length === 0 ? <p className="text-sm text-on-surface-variant">No active sessions reported by the backend.</p> : null}
            </div>
          </div>

          <div className="rounded-[2.5rem] border border-surface-container bg-white shadow-sm">
            <div className="flex flex-col gap-4 border-b border-surface-container p-8 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <h2 className="text-2xl font-black tracking-tight text-primary">All session records</h2>
                <p className="mt-1 text-sm text-on-surface-variant">Search charger IDs, transaction IDs, or user tags.</p>
              </div>
              <div className="relative w-full lg:w-80">
                <span className="material-symbols-outlined absolute left-4 top-3 text-outline">search</span>
                <input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  type="text"
                  placeholder="Search sessions"
                  className="w-full rounded-2xl border border-surface-container bg-surface-container-low py-3 pl-12 pr-4 text-sm font-semibold outline-none focus:border-secondary"
                />
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-surface-container-low text-[10px] uppercase tracking-[0.2em] text-outline">
                  <tr>
                    <th className="px-8 py-5">Transaction</th>
                    <th className="px-6 py-5">Charger</th>
                    <th className="px-6 py-5">User</th>
                    <th className="px-6 py-5">Started</th>
                    <th className="px-6 py-5 text-right">Energy</th>
                    <th className="px-8 py-5">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredSessions.map((session) => (
                    <tr key={session.id} className="border-t border-surface-container">
                      <td className="px-8 py-5">
                        <Link href={`/sessions/${session.id}`} className="font-black text-primary hover:text-secondary">
                          #{session.transaction_id}
                        </Link>
                      </td>
                      <td className="px-6 py-5">
                        <Link href={`/sites/${session.charger_id}`} className="font-semibold text-primary hover:text-secondary">
                          {session.charger_id}
                        </Link>
                      </td>
                      <td className="px-6 py-5 text-on-surface-variant">{session.id_tag || 'Guest / Public'}</td>
                      <td className="px-6 py-5 text-on-surface-variant">{formatDateTime(session.start_time)}</td>
                      <td className="px-6 py-5 text-right font-bold text-primary">{formatNumber(session.energy_kwh ?? 0)} kWh</td>
                      <td className="px-8 py-5">
                        <StatusBadge label={session.active ? 'Charging' : 'Stopped'} />
                      </td>
                    </tr>
                  ))}

                  {!isLoading && filteredSessions.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-8 py-12 text-center text-on-surface-variant">
                        No sessions matched the current filter.
                      </td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
