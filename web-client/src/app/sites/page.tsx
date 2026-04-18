"use client";

import Link from 'next/link';
import type { FormEvent } from 'react';
import { useMemo, useState } from 'react';

import MetricCard from '@/components/MetricCard';
import StatusBadge from '@/components/StatusBadge';
import { useChargers } from '@/hooks/useData';
import { useLiveStream } from '@/hooks/useLiveStream';
import { chargerApi } from '@/lib/api';
import { formatDateTime, formatInteger } from '@/lib/format';
import type { CreateChargerPayload } from '@/lib/types';

const initialForm: CreateChargerPayload = {
  charger_id: '',
  vendor: '',
  model: '',
  serial_number: '',
  firmware_version: '',
  ocpp_version: '1.6',
};

export default function SiteManagement() {
  useLiveStream({
    keys: ['/chargers'],
  });

  const { chargers, count, isLoading, isError, refresh } = useChargers();
  const [query, setQuery] = useState('');
  const [form, setForm] = useState<CreateChargerPayload>(initialForm);
  const [isSaving, setIsSaving] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  const filteredChargers = useMemo(() => {
    const value = query.trim().toLowerCase();
    if (!value) {
      return chargers;
    }

    return chargers.filter((charger) =>
      [charger.charger_id, charger.vendor, charger.model, charger.ocpp_version]
        .filter(Boolean)
        .some((item) => item.toLowerCase().includes(value)),
    );
  }, [chargers, query]);

  async function handleCreateCharger(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    setFeedback(null);

    try {
      await chargerApi.create({
        ...form,
        charger_id: form.charger_id.trim(),
        vendor: form.vendor?.trim(),
        model: form.model?.trim(),
        serial_number: form.serial_number?.trim(),
        firmware_version: form.firmware_version?.trim(),
      });
      setForm(initialForm);
      setFeedback('Charger created successfully.');
      await refresh();
    } catch {
      setFeedback('Failed to create charger. Check the backend response and try again.');
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDeleteCharger(chargerId: string) {
    setFeedback(null);

    try {
      await chargerApi.remove(chargerId);
      setFeedback(`Deleted charger ${chargerId}.`);
      await refresh();
    } catch {
      setFeedback(`Failed to delete charger ${chargerId}.`);
    }
  }

  if (isError) {
    return (
      <div className="flex min-h-screen flex-1 items-center justify-center bg-surface-container-lowest">
        <div className="rounded-[2rem] border border-error/20 bg-white p-8 text-center shadow-xl">
          <span className="material-symbols-outlined text-6xl text-error">dns</span>
          <h2 className="mt-4 text-2xl font-bold text-primary">Registry Unavailable</h2>
          <p className="mt-2 text-on-surface-variant">Unable to synchronize chargers from the backend.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 bg-surface-container-lowest">
      <section className="mx-auto flex max-w-[1600px] flex-col gap-8 px-4 md:px-8 pb-24 md:pb-12 pt-24 md:pt-28">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="mt-3 text-4xl font-bold tracking-tight text-primary">Charger management and hardware inventory</h1>
            <p className="mt-2 max-w-2xl text-sm font-medium text-on-surface-variant">
              Frontend is now wired to charger CRUD, per-charger detail, sessions, command history, and meter data from the backend API.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          <MetricCard label="Registered Chargers" value={isLoading ? '..' : formatInteger(count)} hint="Total rows from charger registry" />
          <MetricCard
            label="Available or Charging"
            value={isLoading ? '..' : formatInteger(chargers.filter((charger) => ['Available', 'Charging'].includes(charger.status)).length)}
            hint="Operational fleet units"
          />
          <MetricCard
            label="Faulted or Offline"
            value={isLoading ? '..' : formatInteger(chargers.filter((charger) => ['Faulted', 'Unavailable'].includes(charger.status)).length)}
            hint="Units needing operator review"
          />
        </div>

        <div className="grid grid-cols-1 gap-8 xl:grid-cols-[1.1fr_1.8fr]">
          <form onSubmit={handleCreateCharger} className="rounded-[2.5rem] border border-surface-container bg-white p-8 shadow-sm">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-2xl font-bold tracking-tight text-primary">Register charger</h2>
                <p className="mt-1 text-sm text-on-surface-variant">Uses `POST /api/chargers` without backend changes.</p>
              </div>
            </div>

            <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
              <label className="block">
                <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-outline">Charger ID</span>
                <input
                  required
                  value={form.charger_id}
                  onChange={(event) => setForm((current) => ({ ...current, charger_id: event.target.value }))}
                  className="mt-2 w-full rounded-2xl border border-surface-container bg-surface-container-low px-4 py-3 text-sm font-semibold outline-none focus:border-secondary"
                />
              </label>
              <label className="block">
                <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-outline">OCPP Version</span>
                <select
                  value={form.ocpp_version}
                  onChange={(event) => setForm((current) => ({ ...current, ocpp_version: event.target.value }))}
                  className="mt-2 w-full rounded-2xl border border-surface-container bg-surface-container-low px-4 py-3 text-sm font-semibold outline-none focus:border-secondary"
                >
                  <option value="1.6">1.6</option>
                  <option value="2.0.1">2.0.1</option>
                </select>
              </label>
              <label className="block">
                <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-outline">Vendor</span>
                <input
                  value={form.vendor}
                  onChange={(event) => setForm((current) => ({ ...current, vendor: event.target.value }))}
                  className="mt-2 w-full rounded-2xl border border-surface-container bg-surface-container-low px-4 py-3 text-sm font-semibold outline-none focus:border-secondary"
                />
              </label>
              <label className="block">
                <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-outline">Model</span>
                <input
                  value={form.model}
                  onChange={(event) => setForm((current) => ({ ...current, model: event.target.value }))}
                  className="mt-2 w-full rounded-2xl border border-surface-container bg-surface-container-low px-4 py-3 text-sm font-semibold outline-none focus:border-secondary"
                />
              </label>
              <label className="block">
                <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-outline">Serial Number</span>
                <input
                  value={form.serial_number}
                  onChange={(event) => setForm((current) => ({ ...current, serial_number: event.target.value }))}
                  className="mt-2 w-full rounded-2xl border border-surface-container bg-surface-container-low px-4 py-3 text-sm font-semibold outline-none focus:border-secondary"
                />
              </label>
              <label className="block">
                <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-outline">Firmware Version</span>
                <input
                  value={form.firmware_version}
                  onChange={(event) => setForm((current) => ({ ...current, firmware_version: event.target.value }))}
                  className="mt-2 w-full rounded-2xl border border-surface-container bg-surface-container-low px-4 py-3 text-sm font-semibold outline-none focus:border-secondary"
                />
              </label>
            </div>

            <div className="mt-6 flex items-center justify-between gap-4">
              <div className="text-sm font-medium text-on-surface-variant">{feedback ?? 'New chargers become visible immediately after refresh.'}</div>
              <button
                type="submit"
                disabled={isSaving}
                className="rounded-2xl bg-primary px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-primary/20 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isSaving ? 'Saving...' : 'Create Charger'}
              </button>
            </div>
          </form>

          <div className="rounded-[2.5rem] border border-surface-container bg-white shadow-sm">
            <div className="flex flex-col gap-4 border-b border-surface-container p-8 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <h2 className="text-2xl font-bold tracking-tight text-primary">Hardware catalog</h2>
                <p className="mt-1 text-sm text-on-surface-variant">Open any charger to view stats, remote commands, sessions, and meter values.</p>
              </div>
              <div className="relative w-full lg:w-80">
                <span className="material-symbols-outlined absolute left-4 top-3 text-outline">manage_search</span>
                <input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  type="text"
                  placeholder="Search charger, vendor, model"
                  className="w-full rounded-2xl border border-surface-container bg-surface-container-low py-3 pl-12 pr-4 text-sm font-semibold outline-none focus:border-secondary"
                />
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-surface-container-low text-[10px] uppercase tracking-[0.2em] text-outline">
                  <tr>
                    <th className="px-8 py-5">Charger</th>
                    <th className="px-6 py-5">Vendor / Model</th>
                    <th className="px-6 py-5">Protocol</th>
                    <th className="px-6 py-5">Heartbeat</th>
                    <th className="px-6 py-5">Status</th>
                    <th className="px-8 py-5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredChargers.map((charger) => (
                    <tr key={charger.id} className="border-t border-surface-container">
                      <td className="px-8 py-5">
                        <Link href={`/sites/${charger.charger_id}`} className="font-semibold text-primary hover:text-secondary">
                          {charger.charger_id}
                        </Link>
                      </td>
                      <td className="px-6 py-5 font-medium text-on-surface-variant">{charger.vendor} · {charger.model}</td>
                      <td className="px-6 py-5 font-semibold text-primary">OCPP {charger.ocpp_version}</td>
                      <td className="px-6 py-5 text-on-surface-variant">{formatDateTime(charger.last_heartbeat)}</td>
                      <td className="px-6 py-5">
                        <StatusBadge label={charger.status} />
                      </td>
                      <td className="px-8 py-5">
                        <div className="flex justify-end gap-3">
                          <Link href={`/sites/${charger.charger_id}`} className="rounded-xl border border-surface-container px-4 py-2 font-bold text-primary">
                            Open
                          </Link>
                          <button
                            type="button"
                            onClick={() => handleDeleteCharger(charger.charger_id)}
                            className="rounded-xl border border-error/20 px-4 py-2 font-bold text-error"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}

                  {!isLoading && filteredChargers.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-8 py-12 text-center text-on-surface-variant">
                        No chargers matched the current filter.
                      </td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
