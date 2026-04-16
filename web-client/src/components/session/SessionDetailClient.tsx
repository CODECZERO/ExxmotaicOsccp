"use client";

import Link from 'next/link';
import { useState } from 'react';

import KeyValueGrid from '@/components/KeyValueGrid';
import MetricCard from '@/components/MetricCard';
import StatusBadge from '@/components/StatusBadge';
import { useSession, useSessionMeterValues } from '@/hooks/useData';
import { useLiveStream } from '@/hooks/useLiveStream';
import { sessionApi } from '@/lib/api';
import { formatDateTime, formatInteger, formatNumber, formatPercent } from '@/lib/format';

interface SessionDetailClientProps {
  sessionId: string;
}

export default function SessionDetailClient({ sessionId }: SessionDetailClientProps) {
  useLiveStream({
    sessionId,
    keys: [`/sessions/${sessionId}`, `/sessions/${sessionId}/meter-values`, '/sessions/active', '/stats'],
  });

  const { session, isLoading, isError, refresh } = useSession(sessionId, {
    refreshInterval: (data) => data?.session.active ? 2500 : 15000,
  });
  const { meterValues, refresh: refreshMeterValues } = useSessionMeterValues(sessionId, {
    refreshInterval: session?.active ? 2500 : 10000,
  });
  const [isStopping, setIsStopping] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  async function handleStopSession() {
    setIsStopping(true);
    setFeedback(null);

    try {
      await sessionApi.stop(sessionId);
      await Promise.all([refresh(), refreshMeterValues()]);
      setFeedback('Session stop request completed.');
    } catch {
      setFeedback('Failed to stop session.');
    } finally {
      setIsStopping(false);
    }
  }

  if (isError) {
    return (
      <div className="flex min-h-screen flex-1 items-center justify-center bg-surface-container-lowest">
        <div className="rounded-[2rem] border border-error/20 bg-white p-8 text-center shadow-xl">
          <span className="material-symbols-outlined text-6xl text-error">error</span>
          <h2 className="mt-4 text-2xl font-black text-primary">Session not found</h2>
          <p className="mt-2 text-on-surface-variant">No session details were returned for {sessionId}.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 bg-surface-container-lowest">
      <div className="mx-auto flex max-w-[1600px] flex-col gap-8 px-8 pb-12 pt-28">
        <section className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <Link href="/sessions" className="text-[11px] font-black uppercase tracking-[0.3em] text-secondary">
              Back to sessions
            </Link>
            <div className="mt-3 flex flex-wrap items-center gap-4">
              <h1 className="text-4xl font-black tracking-tight text-primary">Session #{session?.transaction_id ?? sessionId}</h1>
              <StatusBadge label={session?.active ? 'Charging' : 'Stopped'} />
            </div>
            <p className="mt-2 text-sm font-medium text-on-surface-variant">Single session detail using backend session and meter value endpoints.</p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {session?.charger_id ? (
              <Link href={`/sites/${session.charger_id}`} className="rounded-2xl border border-surface-container bg-white px-5 py-3 text-sm font-black text-primary shadow-sm">
                Open charger
              </Link>
            ) : null}
            {session?.active ? (
              <button
                type="button"
                onClick={handleStopSession}
                disabled={isStopping}
                className="rounded-2xl bg-error px-5 py-3 text-sm font-black text-white disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isStopping ? 'Stopping...' : 'Stop Session'}
              </button>
            ) : null}
          </div>
        </section>

        <section className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Energy" value={`${formatNumber(session?.energy_kwh ?? 0)} kWh`} hint="Computed session energy" />
          <MetricCard label="Connector" value={formatInteger(session?.connector_id ?? 0)} hint="Connector used for transaction" />
          <MetricCard label="Meter Start" value={formatInteger(session?.meter_start ?? 0)} hint="Initial meter reading" />
          <MetricCard label="Meter Stop" value={formatInteger(session?.meter_stop ?? 0)} hint="Latest stop reading" />
        </section>

        <section className="grid grid-cols-1 gap-8 xl:grid-cols-[1fr_1fr]">
          <div className="rounded-[2.5rem] border border-surface-container bg-white p-8 shadow-sm">
            <h2 className="text-2xl font-black tracking-tight text-primary">Session profile</h2>
            <p className="mt-1 text-sm text-on-surface-variant">Served by `GET /api/sessions/:id`.</p>
            <div className="mt-6">
              <KeyValueGrid
                items={[
                  { label: 'Session ID', value: session?.id ? String(session.id) : sessionId },
                  { label: 'Transaction ID', value: session?.transaction_id || '--' },
                  { label: 'Charger ID', value: session?.charger_id || '--' },
                  { label: 'User ID Tag', value: session?.id_tag || 'Guest / Public' },
                  { label: 'Start Time', value: formatDateTime(session?.start_time) },
                  { label: 'Stop Time', value: formatDateTime(session?.stop_time) },
                  { label: 'Stop Reason', value: session?.stop_reason || '--' },
                  { label: 'EVSE ID', value: formatInteger(session?.evse_id ?? 0) },
                  { label: 'Created At', value: formatDateTime(session?.created_at) },
                ]}
              />
            </div>
            <p className="mt-6 text-sm font-medium text-on-surface-variant">{feedback ?? 'Use the stop action only for active backend sessions.'}</p>
          </div>

          <div className="rounded-[2.5rem] border border-surface-container bg-white p-8 shadow-sm">
            <h2 className="text-2xl font-black tracking-tight text-primary">Meter value summary</h2>
            <p className="mt-1 text-sm text-on-surface-variant">Historical readings from `GET /api/sessions/:id/meter-values`.</p>

            <div className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
              <div className="rounded-2xl border border-surface-container bg-surface-container-low p-4">
                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-outline">Samples</p>
                <p className="mt-2 text-2xl font-black text-primary">{formatInteger(meterValues.length)}</p>
              </div>
              <div className="rounded-2xl border border-surface-container bg-surface-container-low p-4">
                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-outline">Peak Power</p>
                <p className="mt-2 text-2xl font-black text-primary">
                  {formatInteger(Math.max(0, ...meterValues.map((reading) => reading.power_w ?? 0)))} W
                </p>
              </div>
              <div className="rounded-2xl border border-surface-container bg-surface-container-low p-4">
                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-outline">Latest Voltage</p>
                <p className="mt-2 text-2xl font-black text-primary">{formatNumber(meterValues[0]?.voltage ?? 0)} V</p>
              </div>
              <div className="rounded-2xl border border-surface-container bg-surface-container-low p-4">
                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-outline">Latest SOC</p>
                <p className="mt-2 text-2xl font-black text-primary">{formatPercent(meterValues[0]?.soc ?? 0)}</p>
              </div>
            </div>
          </div>
        </section>

        <section className="rounded-[2.5rem] border border-surface-container bg-white p-8 shadow-sm">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h2 className="text-2xl font-black tracking-tight text-primary">Meter value timeline</h2>
              <p className="mt-1 text-sm text-on-surface-variant">Every reading attached to this session, newest first.</p>
            </div>
            <span className="rounded-full bg-surface-container px-3 py-1 text-[10px] font-black uppercase tracking-[0.2em] text-primary">
              {isLoading ? 'Loading' : `${meterValues.length} readings`}
            </span>
          </div>

          <div className="mt-6 overflow-x-auto rounded-[2rem] border border-surface-container">
            <table className="w-full text-left text-sm">
              <thead className="bg-surface-container-low text-[10px] uppercase tracking-[0.2em] text-outline">
                <tr>
                  <th className="px-6 py-4">Timestamp</th>
                  <th className="px-6 py-4">Energy (Wh)</th>
                  <th className="px-6 py-4">Power (W)</th>
                  <th className="px-6 py-4">Voltage</th>
                  <th className="px-6 py-4">Current</th>
                  <th className="px-6 py-4">SOC</th>
                </tr>
              </thead>
              <tbody>
                {meterValues.map((reading) => (
                  <tr key={reading.id} className="border-t border-surface-container">
                    <td className="px-6 py-4 font-medium text-on-surface-variant">{formatDateTime(reading.timestamp)}</td>
                    <td className="px-6 py-4 font-semibold text-primary">{formatNumber(reading.energy_wh ?? 0, 0)}</td>
                    <td className="px-6 py-4 text-primary">{formatNumber(reading.power_w ?? 0, 0)}</td>
                    <td className="px-6 py-4 text-primary">{formatNumber(reading.voltage ?? 0)}</td>
                    <td className="px-6 py-4 text-primary">{formatNumber(reading.current_a ?? 0)}</td>
                    <td className="px-6 py-4 text-primary">{formatPercent(reading.soc ?? 0)}</td>
                  </tr>
                ))}
                {meterValues.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-10 text-center text-on-surface-variant">
                      No meter values found for this session.
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );
}
