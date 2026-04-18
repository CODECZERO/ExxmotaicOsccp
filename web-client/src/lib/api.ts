import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5050/api';

const api = axios.create({
  baseURL: API_BASE_URL,
});

export const fetcher = (url: string) => api.get(url).then((res) => res.data);

export const commandApi = {
  start: (chargerId: string, payload: any) => api.post(`/chargers/${chargerId}/start`, payload),
  stop: (chargerId: string, payload: any) => api.post(`/chargers/${chargerId}/stop`, payload),
  reset: (chargerId: string, payload: any) => api.post(`/chargers/${chargerId}/reset`, payload),
  unlock: (chargerId: string, payload: any) => api.post(`/chargers/${chargerId}/unlock`, payload),
};

export const chargerApi = {
  create: (payload: any) => api.post(`/chargers`, payload),
  update: (chargerId: string, payload: any) => api.put(`/chargers/${chargerId}`, payload),
  remove: (chargerId: string) => api.delete(`/chargers/${chargerId}`),
};

export const sessionApi = {
  stop: (sessionId: string) => api.post(`/sessions/${sessionId}/stop`),
};

export function buildLiveStreamUrl(options: { chargerId?: string; sessionId?: string }) {
  const params = new URLSearchParams();
  if (options.chargerId) params.set('charger_id', options.chargerId);
  if (options.sessionId) params.set('session_id', options.sessionId);
  
  const queryString = params.toString();
  return queryString ? `${API_BASE_URL}/live/stream?${queryString}` : `${API_BASE_URL}/live/stream`;
}
