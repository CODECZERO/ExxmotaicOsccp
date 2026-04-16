import useSWR from 'swr';

import { commandApi, fetcher } from '@/lib/api';
import {
  activeSessionsRefreshInterval,
  buildLiveConfig,
  chargerRefreshInterval,
  chargersRefreshInterval,
  chargerStatsRefreshInterval,
  dashboardRefreshInterval,
  latestMeterRefreshInterval,
  meterValuesRefreshInterval,
  sessionRefreshInterval,
  sessionsRefreshInterval,
} from '@/lib/live';
import type {
  Charger,
  ChargerResponse,
  ChargerStatsResponse,
  ChargersResponse,
  ChargingSession,
  CommandLogsResponse,
  DashboardStats,
  DashboardStatsResponse,
  LatestMeterValueResponse,
  MeterValue,
  MeterValuesResponse,
  SessionResponse,
  SessionsResponse,
} from '@/lib/types';

interface LiveQueryOptions<T> {
  refreshInterval?: number | ((data: T | undefined) => number);
}

export function useDashboardStats() {
  const { data, error, isLoading, mutate } = useSWR<DashboardStatsResponse>(
    '/stats',
    fetcher,
    buildLiveConfig(dashboardRefreshInterval),
  );

  return {
    stats: data?.stats as DashboardStats | undefined,
    isLoading,
    isError: error,
    refresh: mutate,
  };
}

export function useChargers() {
  const { data, error, isLoading, mutate } = useSWR<ChargersResponse>(
    '/chargers',
    fetcher,
    buildLiveConfig(chargersRefreshInterval),
  );

  return {
    chargers: data?.chargers ?? [],
    count: data?.count ?? 0,
    isLoading,
    isError: error,
    refresh: mutate,
  };
}

export function useCharger(chargerId?: string, options?: LiveQueryOptions<ChargerResponse>) {
  const shouldFetch = Boolean(chargerId);
  const { data, error, isLoading, mutate } = useSWR<ChargerResponse>(
    shouldFetch ? `/chargers/${chargerId}` : null,
    fetcher,
    buildLiveConfig(options?.refreshInterval ?? chargerRefreshInterval),
  );

  return {
    charger: data?.charger as Charger | undefined,
    isLoading,
    isError: error,
    refresh: mutate,
  };
}

export function useChargerStats(chargerId?: string, options?: LiveQueryOptions<ChargerStatsResponse>) {
  const shouldFetch = Boolean(chargerId);
  const { data, error, isLoading, mutate } = useSWR<ChargerStatsResponse>(
    shouldFetch ? `/chargers/${chargerId}/stats` : null,
    fetcher,
    buildLiveConfig(options?.refreshInterval ?? chargerStatsRefreshInterval),
  );

  return {
    charger: data?.charger,
    stats: data?.stats,
    isLoading,
    isError: error,
    refresh: mutate,
  };
}

export function useSessions() {
  const { data, error, isLoading, mutate } = useSWR<SessionsResponse>(
    '/sessions',
    fetcher,
    buildLiveConfig(sessionsRefreshInterval),
  );

  return {
    sessions: data?.sessions ?? [],
    count: data?.count ?? 0,
    isLoading,
    isError: error,
    refresh: mutate,
  };
}

export function useActiveSessions() {
  const { data, error, isLoading, mutate } = useSWR<SessionsResponse>(
    '/sessions/active',
    fetcher,
    buildLiveConfig(activeSessionsRefreshInterval),
  );

  return {
    sessions: data?.sessions ?? [],
    count: data?.count ?? 0,
    isLoading,
    isError: error,
    refresh: mutate,
  };
}

export function useSession(sessionId?: string, options?: LiveQueryOptions<SessionResponse>) {
  const shouldFetch = Boolean(sessionId);
  const { data, error, isLoading, mutate } = useSWR<SessionResponse>(
    shouldFetch ? `/sessions/${sessionId}` : null,
    fetcher,
    buildLiveConfig(options?.refreshInterval ?? sessionRefreshInterval),
  );

  return {
    session: data?.session as ChargingSession | undefined,
    isLoading,
    isError: error,
    refresh: mutate,
  };
}

export function useChargerSessions(chargerId?: string, options?: LiveQueryOptions<SessionsResponse>) {
  const shouldFetch = Boolean(chargerId);
  const { data, error, isLoading, mutate } = useSWR<SessionsResponse>(
    shouldFetch ? `/chargers/${chargerId}/sessions` : null,
    fetcher,
    buildLiveConfig(options?.refreshInterval ?? sessionsRefreshInterval),
  );

  return {
    sessions: data?.sessions ?? [],
    count: data?.count ?? 0,
    isLoading,
    isError: error,
    refresh: mutate,
  };
}

export function useCommandLogs(chargerId?: string, options?: LiveQueryOptions<CommandLogsResponse>) {
  const shouldFetch = Boolean(chargerId);
  const { data, error, isLoading, mutate } = useSWR<CommandLogsResponse>(
    shouldFetch ? `/chargers/${chargerId}/commands` : null,
    fetcher,
    buildLiveConfig(options?.refreshInterval ?? 7000),
  );

  return {
    commandLogs: data?.command_logs ?? [],
    count: data?.count ?? 0,
    isLoading,
    isError: error,
    refresh: mutate,
  };
}

export function useChargerMeterValues(chargerId?: string, options?: LiveQueryOptions<MeterValuesResponse>) {
  const shouldFetch = Boolean(chargerId);
  const { data, error, isLoading, mutate } = useSWR<MeterValuesResponse>(
    shouldFetch ? `/chargers/${chargerId}/meter-values` : null,
    fetcher,
    buildLiveConfig(options?.refreshInterval ?? meterValuesRefreshInterval),
  );

  return {
    meterValues: data?.meter_values ?? [],
    count: data?.count ?? 0,
    isLoading,
    isError: error,
    refresh: mutate,
  };
}

export function useLatestMeterValue(chargerId?: string, options?: LiveQueryOptions<LatestMeterValueResponse>) {
  const shouldFetch = Boolean(chargerId);
  const { data, error, isLoading, mutate } = useSWR<LatestMeterValueResponse>(
    shouldFetch ? `/chargers/${chargerId}/meter-values/latest` : null,
    fetcher,
    buildLiveConfig(options?.refreshInterval ?? latestMeterRefreshInterval),
  );

  return {
    meterValue: data?.meter_value as MeterValue | undefined,
    isLoading,
    isError: error,
    refresh: mutate,
  };
}

export function useSessionMeterValues(sessionId?: string, options?: LiveQueryOptions<MeterValuesResponse>) {
  const shouldFetch = Boolean(sessionId);
  const { data, error, isLoading, mutate } = useSWR<MeterValuesResponse>(
    shouldFetch ? `/sessions/${sessionId}/meter-values` : null,
    fetcher,
    buildLiveConfig(options?.refreshInterval ?? meterValuesRefreshInterval),
  );

  return {
    meterValues: data?.meter_values ?? [],
    count: data?.count ?? 0,
    isLoading,
    isError: error,
    refresh: mutate,
  };
}

export async function sendRemoteStart(chargerId: string, idTag: string, connectorId = 1) {
  return commandApi.start(chargerId, { id_tag: idTag, connector_id: connectorId });
}

export async function sendRemoteStop(chargerId: string, transactionId?: string) {
  return commandApi.stop(chargerId, { transaction_id: transactionId });
}

export async function sendReset(chargerId: string, type: string) {
  return commandApi.reset(chargerId, { type });
}

export async function sendUnlock(chargerId: string, connectorId = 1) {
  return commandApi.unlock(chargerId, { connector_id: connectorId });
}
