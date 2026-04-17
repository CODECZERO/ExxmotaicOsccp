"use client";

import { startTransition, useEffect, useMemo, useState, useRef, useCallback } from 'react';
import { useSWRConfig } from 'swr';

import { buildLiveStreamUrl } from '@/lib/api';

interface LiveStreamOptions {
  keys: string[];
  chargerId?: string;
  sessionId?: string;
  enabled?: boolean;
}

export function useLiveStream({ keys, chargerId, sessionId, enabled = true }: LiveStreamOptions) {
  const { mutate } = useSWRConfig();
  const [connected, setConnected] = useState(false);

  const streamUrl = useMemo(() => {
    if (!enabled || keys.length === 0) {
      return null;
    }

    return buildLiveStreamUrl({
      chargerId,
      sessionId,
    });
  }, [chargerId, enabled, keys.length, sessionId]);

  const latestKeys = useRef(keys);
  useEffect(() => {
    latestKeys.current = keys;
  }, [keys]);

  const handleUpdate = useCallback(() => {
    setConnected(true);
    startTransition(() => {
      for (const key of latestKeys.current) {
        void mutate(key);
      }
    });
  }, [mutate]);

  const handleOpen = useCallback(() => {
    setConnected(true);
  }, []);

  const handleError = useCallback(() => {
    setConnected(false);
  }, []);

  useEffect(() => {
    if (!streamUrl) {
      return;
    }

    const source = new EventSource(streamUrl);
    source.addEventListener('open', handleOpen);
    source.addEventListener('update', handleUpdate);
    source.addEventListener('ping', handleOpen);
    source.addEventListener('error', handleError);

    return () => {
      source.close();
      setConnected(false);
    };
  }, [streamUrl]);

  return { connected };
}
