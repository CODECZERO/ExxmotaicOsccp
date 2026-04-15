'use client';

import { useEffect } from 'react';

/**
 * ErrorSuppressor
 * 
 * Global client-side component to catch and silence noisy errors originating
 * from browser extensions (MetaMask, Eternl, etc.) which are not caused
 * by the application itself.
 */
export default function ErrorSuppressor() {
  useEffect(() => {
    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      const reason = event.reason?.message || event.reason?.stack || '';
      const isExtensionError = 
        reason.includes('MetaMask') || 
        reason.includes('chrome-extension://') ||
        reason.includes('Eternl');

      if (isExtensionError) {
        // Prevent the error from showing up in the console and dev terminal
        event.preventDefault();
      }
    };

    const handleError = (event: ErrorEvent) => {
      const message = event.message || '';
      const source = event.filename || '';
      const isExtensionError = 
        message.includes('MetaMask') || 
        source.includes('chrome-extension://') ||
        message.includes('dom:receive no data');

      if (isExtensionError) {
        event.preventDefault();
      }
    };

    window.addEventListener('unhandledrejection', handleUnhandledRejection);
    window.addEventListener('error', handleError);

    return () => {
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
      window.removeEventListener('error', handleError);
    };
  }, []);

  return null;
}
