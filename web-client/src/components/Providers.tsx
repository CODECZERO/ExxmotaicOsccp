"use client";

import { SWRConfig } from 'swr';

import { defaultLiveConfig } from '@/lib/live';

interface ProvidersProps {
  children: React.ReactNode;
}

export default function Providers({ children }: ProvidersProps) {
  return <SWRConfig value={defaultLiveConfig}>{children}</SWRConfig>;
}
