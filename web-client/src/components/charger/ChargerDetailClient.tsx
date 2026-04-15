"use client";

import Link from 'next/link';
import type { FormEvent } from 'react';
import { useEffect, useState } from 'react';

import KeyValueGrid from '@/components/KeyValueGrid';
import MetricCard from '@/components/MetricCard';
import StatusBadge from '@/components/StatusBadge';
import {
  useCharger,
  useChargerMeterValues,
  useChargerSessions,
  useChargerStats,
  useCommandLogs,
  useLatestMeterValue,
} from '@/hooks/useData';
import { chargerApi, commandApi } from '@/lib/api';
import { formatDateTime, formatInteger, formatNumber, formatPercent } from '@/lib/format';
import type { UpdateChargerPayload } from '@/lib/types';

interface ChargerDetailClientProps {
  chargerId: string;
}

export default function ChargerDetailClient({ chargerId }: ChargerDetailClientProps) {
  const { charger, isLoading: chargerLoading, isError: chargerError, refresh: refreshCharger } = useCharger(chargerId);
  const { stats, refresh: refreshStats } = useChargerStats(chargerId);
  const { sessions, refresh: refreshSessions } = useChargerSessions(chargerId);
  const { commandLogs, refresh: refreshCommands } = useCommandLogs(chargerId);
  const { meterValues, refresh: refreshMeterValues } = useChargerMeterValues(chargerId);
  const { meterValue, refresh: refreshLatestMeterValue } = useLatestMeterValue(chargerId);

  const [updateForm, setUpdateForm] = useState<UpdateChargerPayload>({
    vendor: '',
    model: '',
    serial_number: '',
    firmware_version: '',
    ocpp_version: '1.6',
    status: 'Available',
  });
  const [commandState, setCommandState] = useState({
    idTag: 'USER123',
    connectorId: '1',
    transactionId: '',
    resetType: 'Soft',
  });
  const [feedback, setFeedback] = useState<string | null>(null);
  const [busyAction, setBusyAction] = useState<string | null>(null);

  useEffect(() => {
    if (!charger) {
      return;
    }

    setUpdateForm({
      vendor: charger.vendor ?? '',
      model: charger.model ?? '',
      serial_number: charger.serial_number ?? '',
      firmware_version: charger.firmware_version ?? '',
      ocpp_version: charger.ocpp_version ?? '1.6',
      status: charger.status,
    });
  }, [charger]);

  async function refreshAll() {
    await Promise.all([
      refreshCharger(),
      refreshStats(),
      refreshSessions(),
      refreshCommands(),
      refreshMeterValues(),
      refreshLatestMeterValue(),
    ]);
  }

  async function handleUpdate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusyAction('update');
    setFeedback(null);

    try {
      await chargerApi.update(chargerId, {
        ...updateForm,
        vendor: updateForm.vendor?.trim(),
        model: updateForm.model?.trim(),
        serial_number: updateForm.serial_number?.trim(),
        firmware_version: updateForm.firmware_version?.trim(),
      });
      await refreshAll();
      setFeedback('Charger metadata updated.');
    } catch {
      setFeedback('Failed to update charger metadata.');
    } finally {
      setBusyAction(null);
    }
  }

  async function runCommand(action: 'start' | 'stop' | 'reset' | 'unlock') {
    setBusyAction(action);
    setFeedback(null);

    try {
      if (action === 'start') {
        await commandApi.start(chargerId, {
          id_tag: commandState.idTag,
          connector_id: Number(commandState.connectorId) || 1,
        });
      }

      if (action === 'stop') {
        await commandApi.stop(chargerId, {
          transaction_id: commandState.transactionId || undefined,
        });
      }

      if (action === 'reset') {
        await commandApi.reset(chargerId, { type: commandState.resetType });
      }

      if (action === 'unlock') {
        await commandApi.unlock(chargerId, {
          connector_id: Number(commandState.connectorId) || 1,
        });
      }

      await refreshAll();
      setFeedback(`Command ${action} completed successfully.`);
    } catch {
      setFeedback(`Command ${action} failed.`);
    } finally {
      setBusyAction(null);
    }
  }

  if (chargerError) {
    return (
      <div className="flex min-h-screen flex-1 items-center justify-center bg-surface-container-lowest">
        <div className="rounded-[2rem] border border-error/20 bg-white p-8 text-center shadow-xl">
          <span className="material-symbols-outlined text-6xl text-error">error</span>
          <h2 className="mt-4 text-2xl font-black text-primary">Charger not found</h2>
          <p className="mt-2 text-on-surface-variant">The backend did not return charger details for {chargerId}.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 bg-surface-container-lowest">
      <div className="mx-auto flex max-w-[1600px] flex-col gap-8 px-8 pb-12 pt-28">
        <section className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <Link href="/sites" className="text-[11px] font-black uppercase tracking-[0.3em] text-secondary">
              Back to registry
            </Link>
            <div className="mt-3 flex flex-wrap items-center gap-4">
              <h1 className="text-4xl font-black tracking-tight text-primary">{charger?.charger_id ?? chargerId}</h1>
              {charger?.status ? <StatusBadge label={charger.status} /> : null}
            </div>
            <p className="mt-2 text-sm font-medium text-on-surface-variant">
              Charger detail view wired to backend stats, sessions, meter values, and remote command endpoints.
            </p>
          </div>

          <div className="rounded-[2rem] border border-surface-container bg-white p-5 shadow-sm">
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-outline">Latest heartbeat</p>
            <p className="mt-2 text-sm font-semibold text-primary">{chargerLoading ? 'Loading...' : formatDateTime(charger?.last_heartbeat)}</p>
          </div>
        </section>

        <section className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Sessions" value={formatInteger(stats?.total_sessions ?? 0)} hint="All sessions for this charger" />
          <MetricCard label="Active Sessions" value={formatInteger(stats?.active_sessions ?? 0)} hint="Currently open transactions" />
          <MetricCard label="Energy Delivered" value={`${formatNumber(stats?.total_energy_kwh ?? 0)} kWh`} hint="Accumulated session energy" />
          <MetricCard label="Commands Sent" value={formatInteger(stats?.total_commands ?? 0)} hint="Command log records" />
        </section>

        <section className="grid grid-cols-1 gap-8 xl:grid-cols-[1.1fr_1fr]">
          <div className="rounded-[2.5rem] border border-surface-container bg-white p-8 shadow-sm">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-2xl font-black tracking-tight text-primary">Charger profile</h2>
                <p className="mt-1 text-sm text-on-surface-variant">Values come from `GET /api/chargers/:id` and `GET /api/chargers/:id/stats`.</p>
              </div>
            </div>

            <div className="mt-6">
              <KeyValueGrid
                items={[
                  { label: 'Vendor', value: charger?.vendor || '--' },
                  { label: 'Model', value: charger?.model || '--' },
                  { label: 'Serial Number', value: charger?.serial_number || '--' },
                  { label: 'Firmware', value: charger?.firmware_version || '--' },
                  { label: 'OCPP Version', value: charger?.ocpp_version || '--' },
                  { label: 'Meter Readings', value: formatInteger(stats?.total_meter_readings ?? 0) },
                ]}
              />
            </div>

            <div className="mt-8 rounded-[2rem] border border-surface-container bg-surface-container-low p-6">
              <h3 className="text-lg font-black text-primary">Latest meter snapshot</h3>
              <div className="mt-4 grid grid-cols-2 gap-4 lg:grid-cols-4">
                <div>
                  <p className="text-[10px] font-black uppercase tracking-[0.2em] text-outline">Power</p>
                  <p className="mt-2 text-xl font-black text-primary">{formatInteger(meterValue?.power_w ?? 0)} W</p>
                </div>
                <div>
                  <p className="text-[10px] font-black uppercase tracking-[0.2em] text-outline">Voltage</p>
                  <p className="mt-2 text-xl font-black text-primary">{formatNumber(meterValue?.voltage ?? 0)} V</p>
                </div>
                <div>
                  <p className="text-[10px] font-black uppercase tracking-[0.2em] text-outline">Current</p>
                  <p className="mt-2 text-xl font-black text-primary">{formatNumber(meterValue?.current_a ?? 0)} A</p>
                </div>
                <div>
                  <p className="text-[10px] font-black uppercase tracking-[0.2em] text-outline">SOC</p>
                  <p className="mt-2 text-xl font-black text-primary">{formatPercent(meterValue?.soc ?? 0)}</p>
                </div>
              </div>
              <p className="mt-4 text-sm text-on-surface-variant">Timestamp: {formatDateTime(meterValue?.timestamp)}</p>
            </div>
          </div>

          <form onSubmit={handleUpdate} className="rounded-[2.5rem] border border-surface-container bg-white p-8 shadow-sm">
            <h2 className="text-2xl font-black tracking-tight text-primary">Update charger metadata</h2>
            <p className="mt-1 text-sm text-on-surface-variant">Uses `PUT /api/chargers/:id` for operator edits.</p>

            <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
              <label className="block">
                <span className="text-[10px] font-black uppercase tracking-[0.2em] text-outline">Vendor</span>
                <input
                  value={updateForm.vendor}
                  onChange={(event) => setUpdateForm((current) => ({ ...current, vendor: event.target.value }))}
                  className="mt-2 w-full rounded-2xl border border-surface-container bg-surface-container-low px-4 py-3 text-sm font-semibold outline-none focus:border-secondary"
                />
              </label>
              <label className="block">
                <span className="text-[10px] font-black uppercase tracking-[0.2em] text-outline">Model</span>
                <input
                  value={updateForm.model}
                  onChange={(event) => setUpdateForm((current) => ({ ...current, model: event.target.value }))}
                  className="mt-2 w-full rounded-2xl border border-surface-container bg-surface-container-low px-4 py-3 text-sm font-semibold outline-none focus:border-secondary"
                />
              </label>
              <label className="block">
                <span className="text-[10px] font-black uppercase tracking-[0.2em] text-outline">Serial Number</span>
                <input
                  value={updateForm.serial_number}
                  onChange={(event) => setUpdateForm((current) => ({ ...current, serial_number: event.target.value }))}
                  className="mt-2 w-full rounded-2xl border border-surface-container bg-surface-container-low px-4 py-3 text-sm font-semibold outline-none focus:border-secondary"
                />
              </label>
              <label className="block">
                <span className="text-[10px] font-black uppercase tracking-[0.2em] text-outline">Firmware</span>
                <input
                  value={updateForm.firmware_version}
                  onChange={(event) => setUpdateForm((current) => ({ ...current, firmware_version: event.target.value }))}
                  className="mt-2 w-full rounded-2xl border border-surface-container bg-surface-container-low px-4 py-3 text-sm font-semibold outline-none focus:border-secondary"
                />
              </label>
              <label className="block">
                <span className="text-[10px] font-black uppercase tracking-[0.2em] text-outline">OCPP Version</span>
                <select
                  value={updateForm.ocpp_version}
                  onChange={(event) => setUpdateForm((current) => ({ ...current, ocpp_version: event.target.value }))}
                  className="mt-2 w-full rounded-2xl border border-surface-container bg-surface-container-low px-4 py-3 text-sm font-semibold outline-none focus:border-secondary"
                >
                  <option value="1.6">1.6</option>
                  <option value="2.0.1">2.0.1</option>
                </select>
              </label>
              <label className="block">
                <span className="text-[10px] font-black uppercase tracking-[0.2em] text-outline">Status</span>
                <select
                  value={updateForm.status}
                  onChange={(event) => setUpdateForm((current) => ({ ...current, status: event.target.value }))}
                  className="mt-2 w-full rounded-2xl border border-surface-container bg-surface-container-low px-4 py-3 text-sm font-semibold outline-none focus:border-secondary"
                >
                  <option value="Available">Available</option>
                  <option value="Charging">Charging</option>
                  <option value="Preparing">Preparing</option>
                  <option value="Finishing">Finishing</option>
                  <option value="Unavailable">Unavailable</option>
                  <option value="Faulted">Faulted</option>
                </select>
              </label>
            </div>

            <div className="mt-6 flex items-center justify-between gap-4">
              <p className="text-sm font-medium text-on-surface-variant">{feedback ?? 'Changes are persisted directly to the backend charger record.'}</p>
              <button
                type="submit"
                disabled={busyAction === 'update'}
                className="rounded-2xl bg-primary px-6 py-3 text-sm font-black text-white disabled:cursor-not-allowed disabled:opacity-60"
              >
                {busyAction === 'update' ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </form>
        </section>

        <section className="grid grid-cols-1 gap-8 xl:grid-cols-[0.95fr_1.05fr]">
          <div className="rounded-[2.5rem] border border-surface-container bg-white p-8 shadow-sm">
            <h2 className="text-2xl font-black tracking-tight text-primary">Remote commands</h2>
            <p className="mt-1 text-sm text-on-surface-variant">Connected to start, stop, reset, unlock, and command log endpoints.</p>

            <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
              <label className="block">
                <span className="text-[10px] font-black uppercase tracking-[0.2em] text-outline">ID Tag</span>
                <input
                  value={commandState.idTag}
                  onChange={(event) => setCommandState((current) => ({ ...current, idTag: event.target.value }))}
                  className="mt-2 w-full rounded-2xl border border-surface-container bg-surface-container-low px-4 py-3 text-sm font-semibold outline-none focus:border-secondary"
                />
              </label>
              <label className="block">
                <span className="text-[10px] font-black uppercase tracking-[0.2em] text-outline">Connector ID</span>
                <input
                  value={commandState.connectorId}
                  onChange={(event) => setCommandState((current) => ({ ...current, connectorId: event.target.value }))}
                  className="mt-2 w-full rounded-2xl border border-surface-container bg-surface-container-low px-4 py-3 text-sm font-semibold outline-none focus:border-secondary"
                />
              </label>
              <label className="block md:col-span-2">
                <span className="text-[10px] font-black uppercase tracking-[0.2em] text-outline">Transaction ID for remote stop</span>
                <input
                  value={commandState.transactionId}
                  onChange={(event) => setCommandState((current) => ({ ...current, transactionId: event.target.value }))}
                  className="mt-2 w-full rounded-2xl border border-surface-container bg-surface-container-low px-4 py-3 text-sm font-semibold outline-none focus:border-secondary"
                />
              </label>
              <label className="block md:col-span-2">
                <span className="text-[10px] font-black uppercase tracking-[0.2em] text-outline">Reset type</span>
                <select
                  value={commandState.resetType}
                  onChange={(event) => setCommandState((current) => ({ ...current, resetType: event.target.value }))}
                  className="mt-2 w-full rounded-2xl border border-surface-container bg-surface-container-low px-4 py-3 text-sm font-semibold outline-none focus:border-secondary"
                >
                  <option value="Soft">Soft</option>
                  <option value="Hard">Hard</option>
                </select>
              </label>
            </div>

            <div className="mt-6 grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => runCommand('start')}
                disabled={busyAction !== null}
                className="rounded-2xl bg-primary px-4 py-3 text-sm font-black text-white disabled:cursor-not-allowed disabled:opacity-60"
              >
                Remote Start
              </button>
              <button
                type="button"
                onClick={() => runCommand('stop')}
                disabled={busyAction !== null}
                className="rounded-2xl border border-surface-container bg-white px-4 py-3 text-sm font-black text-primary disabled:cursor-not-allowed disabled:opacity-60"
              >
                Remote Stop
              </button>
              <button
                type="button"
                onClick={() => runCommand('unlock')}
                disabled={busyAction !== null}
                className="rounded-2xl border border-surface-container bg-white px-4 py-3 text-sm font-black text-primary disabled:cursor-not-allowed disabled:opacity-60"
              >
                Unlock Connector
              </button>
              <button
                type="button"
                onClick={() => runCommand('reset')}
                disabled={busyAction !== null}
                className="rounded-2xl border border-error/20 bg-error/5 px-4 py-3 text-sm font-black text-error disabled:cursor-not-allowed disabled:opacity-60"
              >
                Reset Charger
              </button>
            </div>

            <p className="mt-4 text-sm font-medium text-on-surface-variant">{feedback ?? 'Commands are written to backend command logs and reflected below.'}</p>
          </div>

          <div className="rounded-[2.5rem] border border-surface-container bg-white p-8 shadow-sm">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-2xl font-black tracking-tight text-primary">Command history</h2>
                <p className="mt-1 text-sm text-on-surface-variant">Live data from `GET /api/chargers/:id/commands`.</p>
              </div>
              <span className="rounded-full bg-surface-container px-3 py-1 text-[10px] font-black uppercase tracking-[0.2em] text-primary">
                {formatInteger(commandLogs.length)} records
              </span>
            </div>

            <div className="mt-6 space-y-3">
              {commandLogs.slice(0, 8).map((log) => (
                <div key={log.id} className="rounded-2xl border border-surface-container bg-surface-container-lowest p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="font-black text-primary">{log.command}</p>
                      <p className="mt-1 text-xs text-on-surface-variant">{formatDateTime(log.created_at)}</p>
                    </div>
                    <StatusBadge label={log.status} />
                  </div>
                </div>
              ))}
              {commandLogs.length === 0 ? <p className="text-sm text-on-surface-variant">No command logs yet for this charger.</p> : null}
            </div>
          </div>
        </section>

        <section className="grid grid-cols-1 gap-8 xl:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-[2.5rem] border border-surface-container bg-white p-8 shadow-sm">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-2xl font-black tracking-tight text-primary">Sessions for this charger</h2>
                <p className="mt-1 text-sm text-on-surface-variant">Directly consuming `GET /api/chargers/:id/sessions`.</p>
              </div>
            </div>

            <div className="mt-6 overflow-hidden rounded-[2rem] border border-surface-container">
              <table className="w-full text-left text-sm">
                <thead className="bg-surface-container-low text-[10px] uppercase tracking-[0.2em] text-outline">
                  <tr>
                    <th className="px-6 py-4">Transaction</th>
                    <th className="px-6 py-4">Started</th>
                    <th className="px-6 py-4 text-right">Energy</th>
                    <th className="px-6 py-4">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {sessions.slice(0, 8).map((session) => (
                    <tr key={session.id} className="border-t border-surface-container">
                      <td className="px-6 py-4 font-semibold text-primary">
                        <Link href={`/sessions/${session.id}`} className="hover:text-secondary">
                          #{session.transaction_id}
                        </Link>
                      </td>
                      <td className="px-6 py-4 text-on-surface-variant">{formatDateTime(session.start_time)}</td>
                      <td className="px-6 py-4 text-right font-bold text-primary">{formatNumber(session.energy_kwh ?? 0)} kWh</td>
                      <td className="px-6 py-4">
                        <StatusBadge label={session.active ? 'Charging' : 'Stopped'} />
                      </td>
                    </tr>
                  ))}
                  {sessions.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="px-6 py-10 text-center text-on-surface-variant">
                        No sessions have been recorded for this charger.
                      </td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </div>
          </div>

          <div className="rounded-[2.5rem] border border-surface-container bg-white p-8 shadow-sm">
            <h2 className="text-2xl font-black tracking-tight text-primary">Recent meter values</h2>
            <p className="mt-1 text-sm text-on-surface-variant">Connected to both historical and latest meter endpoints.</p>

            <div className="mt-6 space-y-3">
              {meterValues.slice(0, 8).map((reading) => (
                <div key={reading.id} className="rounded-2xl border border-surface-container bg-surface-container-lowest p-4">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="font-black text-primary">{formatInteger(reading.power_w ?? 0)} W</p>
                      <p className="mt-1 text-xs text-on-surface-variant">{formatDateTime(reading.timestamp)}</p>
                    </div>
                    <div className="text-right text-sm font-semibold text-primary">
                      <p>{formatNumber(reading.voltage ?? 0)} V</p>
                      <p>{formatNumber(reading.current_a ?? 0)} A</p>
                    </div>
                  </div>
                </div>
              ))}
              {meterValues.length === 0 ? <p className="text-sm text-on-surface-variant">No meter values returned for this charger.</p> : null}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
