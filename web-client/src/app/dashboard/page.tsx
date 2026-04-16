"use client";

import Link from 'next/link';

import MetricCard from '@/components/MetricCard';
import StatusBadge from '@/components/StatusBadge';
import { useActiveSessions, useChargers, useDashboardStats } from '@/hooks/useData';
import { useLiveStream } from '@/hooks/useLiveStream';
import { formatDateTime, formatInteger, formatNumber } from '@/lib/format';

export default function NetworkSummary() {
  useLiveStream({
    keys: ['/stats', '/chargers', '/sessions/active'],
  });

  const { stats, isLoading, isError } = useDashboardStats();
  const { chargers } = useChargers();
  const { sessions: activeSessions } = useActiveSessions();

  if (isError) {
    return (
      <div className="flex min-h-screen flex-1 items-center justify-center bg-surface-container-lowest">
        <div className="rounded-[2rem] border border-error/20 bg-white p-8 text-center shadow-xl">
          <span className="material-symbols-outlined text-6xl text-error">cloud_off</span>
          <h2 className="mt-4 text-2xl font-black text-primary">Backend Unreachable</h2>
          <p className="mt-2 text-on-surface-variant">Dashboard data could not be loaded from the API.</p>
        </div>
      </div>
    );
  }

  const statusEntries = Object.entries(stats?.chargers.by_status ?? {});
  const versionEntries = Object.entries(stats?.chargers.by_version ?? {});

  return (
    <div className="flex-1 bg-surface-container-lowest">
      <div className="mx-auto flex max-w-[1600px] flex-col gap-8 px-8 pb-12 pt-28">
        <section className="flex flex-col justify-between gap-6 lg:flex-row lg:items-end">
          <div>
            <h1 className="mt-3 text-4xl font-black tracking-tight text-primary">EV network command center</h1>
            <p className="mt-2 max-w-2xl text-sm font-medium text-on-surface-variant">
              Live backend statistics, active charger health, session throughput, and recent activity from the OCPP platform.
            </p>
          </div>
        </section>

        <section className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            label="Total Chargers"
            value={isLoading ? '..' : formatInteger(stats?.chargers.total ?? 0)}
            hint="Registered physical chargers"
          />
          <MetricCard
            label="Online Chargers"
            value={isLoading ? '..' : formatInteger(stats?.chargers.online ?? 0)}
            hint="Chargers not marked unavailable"
          />
          <MetricCard
            label="Active Sessions"
            value={isLoading ? '..' : formatInteger(stats?.sessions.active ?? 0)}
            hint="Live transactions drawing load"
          />
          <MetricCard
            label="Energy Delivered"
            value={isLoading ? '..' : `${formatNumber(stats?.sessions.total_energy_kwh ?? 0, 2)} kWh`}
            hint="Accumulated session energy"
          />
        </section>

        <section className="grid grid-cols-1 gap-8 xl:grid-cols-[1.4fr_1fr]">
          <div className="rounded-[2.5rem] border border-surface-container bg-white p-8 shadow-sm">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-2xl font-black tracking-tight text-primary">Active sessions</h2>
                <p className="mt-1 text-sm text-on-surface-variant">Using `GET /api/sessions/active` with direct session links.</p>
              </div>
              <Link href="/sessions" className="rounded-xl bg-primary px-4 py-2 text-sm font-bold text-white">
                View all sessions
              </Link>
            </div>

            <div className="mt-6 overflow-hidden rounded-[2rem] border border-surface-container">
              <table className="w-full text-left text-sm">
                <thead className="bg-surface-container-low text-[10px] uppercase tracking-[0.2em] text-outline">
                  <tr>
                    <th className="px-6 py-4">Session</th>
                    <th className="px-6 py-4">Charger</th>
                    <th className="px-6 py-4">Started</th>
                    <th className="px-6 py-4 text-right">Energy</th>
                  </tr>
                </thead>
                <tbody>
                  {activeSessions.slice(0, 6).map((session) => (
                    <tr key={session.id} className="border-t border-surface-container">
                      <td className="px-6 py-4 font-semibold text-primary">
                        <Link href={`/sessions/${session.id}`} className="hover:text-secondary">
                          #{session.transaction_id}
                        </Link>
                      </td>
                      <td className="px-6 py-4">
                        <Link href={`/sites/${session.charger_id}`} className="font-semibold text-primary hover:text-secondary">
                          {session.charger_id}
                        </Link>
                      </td>
                      <td className="px-6 py-4 text-on-surface-variant">{formatDateTime(session.start_time)}</td>
                      <td className="px-6 py-4 text-right font-bold text-primary">{formatNumber(session.energy_kwh ?? 0, 2)} kWh</td>
                    </tr>
                  ))}
                  {!isLoading && activeSessions.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="px-6 py-10 text-center text-on-surface-variant">
                        No active sessions are currently reported by the backend.
                      </td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </div>
          </div>

          <div className="space-y-8">
            <div className="rounded-[2.5rem] border border-surface-container bg-white p-8 shadow-sm">
              <h2 className="text-2xl font-black tracking-tight text-primary">Status distribution</h2>
              <div className="mt-6 space-y-3">
                {statusEntries.length > 0 ? (
                  statusEntries.map(([status, count]) => (
                    <div key={status} className="flex items-center justify-between rounded-2xl bg-surface-container-low px-4 py-3">
                      <StatusBadge label={status} />
                      <span className="text-lg font-black text-primary">{formatInteger(count)}</span>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-on-surface-variant">No charger status data available.</p>
                )}
              </div>
            </div>

            <div className="rounded-[2.5rem] border border-surface-container bg-white p-8 shadow-sm">
              <h2 className="text-2xl font-black tracking-tight text-primary">Protocol versions</h2>
              <div className="mt-6 space-y-3">
                {versionEntries.length > 0 ? (
                  versionEntries.map(([version, count]) => (
                    <div key={version} className="flex items-center justify-between rounded-2xl bg-surface-container-low px-4 py-3">
                      <span className="text-sm font-black uppercase tracking-[0.2em] text-outline">OCPP {version}</span>
                      <span className="text-lg font-black text-primary">{formatInteger(count)}</span>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-on-surface-variant">No protocol distribution data available.</p>
                )}
              </div>
            </div>
          </div>
        </section>

        <section className="rounded-[2.5rem] border border-surface-container bg-white p-8 shadow-sm">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h2 className="text-2xl font-black tracking-tight text-primary">Recently seen chargers</h2>
              <p className="mt-1 text-sm text-on-surface-variant">Using the live charger registry returned by `GET /api/chargers`.</p>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
            {chargers.slice(0, 6).map((charger) => (
              <Link
                key={charger.id}
                href={`/sites/${charger.charger_id}`}
                className="rounded-[1.75rem] border border-surface-container bg-surface-container-lowest p-5 transition hover:border-secondary hover:shadow-sm"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-lg font-black tracking-tight text-primary">{charger.charger_id}</p>
                    <p className="mt-1 text-sm font-medium text-on-surface-variant">{charger.vendor} · {charger.model}</p>
                  </div>
                  <StatusBadge label={charger.status} />
                </div>
                <div className="mt-4 text-xs font-semibold uppercase tracking-[0.2em] text-outline">
                  Last heartbeat: {formatDateTime(charger.last_heartbeat)}
                </div>
              </Link>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
