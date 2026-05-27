import axios from 'axios';

const BASE_URL = import.meta.env['VITE_API_BASE_URL'] ?? 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30_000,
});

let getTokenFn: (() => Promise<string | null>) | null = null;

export function setTokenProvider(fn: () => Promise<string | null>) {
  getTokenFn = fn;
}

// Impersonation token provider — set from ImpersonationProvider on mount
let getImpersonationTokenFn: (() => string | null) | null = null;

export function setImpersonationTokenProvider(fn: () => string | null) {
  getImpersonationTokenFn = fn;
}

apiClient.interceptors.request.use(async (config) => {
  if (getTokenFn) {
    try {
      const token = await getTokenFn();
      if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
      }
    } catch {
      // Clerk not yet initialized — send request without token (dev bypass handles it)
    }
  }

  // Inject impersonation token when active
  if (getImpersonationTokenFn) {
    const impersonationToken = getImpersonationTokenFn();
    if (impersonationToken) {
      config.headers['X-Impersonation-Token'] = impersonationToken;
    }
  }

  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      // Let Clerk handle auth redirect
      window.location.href = '/sign-in';
    }
    return Promise.reject(error);
  }
);
