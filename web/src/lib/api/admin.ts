/**
 * Admin API client — typed wrappers for platform-operator endpoints.
 *
 * Injects X-Impersonation-Token header when an active impersonation token
 * is available via the impersonation context ref.
 */
import { apiClient } from './client';

// ── Types ──────────────────────────────────────────────────────────────────────

export interface AdminFunnelRow {
  tenant_id: string;
  tenant_name: string;
  current_step: string;
  connected_integrations: string[];
  drop_off_flag: boolean;
  activated_at: string | null;
  activation_timing: number | null; // seconds from signup to activation
  time_in_current_step_seconds: number | null;
}

export interface SurveyResponseRow {
  tenant_id: string;
  tenant_name: string;
  pain_option: string;
  free_text: string | null;
  answered_at: string;
}

export interface ImpersonationTokenResponse {
  token: string;
  expires_at: string;
  target_tenant_name: string;
}

// ── API Functions ──────────────────────────────────────────────────────────────

/**
 * Fetch the onboarding funnel table for all tenants.
 * Requires platform_operator claim in JWT.
 */
export async function fetchFunnel(): Promise<AdminFunnelRow[]> {
  const response = await apiClient.get<{ rows: AdminFunnelRow[] }>('/admin/funnel');
  return response.data.rows;
}

/**
 * Fetch all survey responses.
 * Requires platform_operator claim in JWT.
 */
export async function fetchSurveyResponses(): Promise<SurveyResponseRow[]> {
  const response = await apiClient.get<{ responses: SurveyResponseRow[] }>(
    '/admin/survey-responses'
  );
  return response.data.responses;
}

/**
 * Start an impersonation session for the given org.
 * Returns a short-lived token and expiry.
 */
export async function startImpersonation(orgId: string): Promise<ImpersonationTokenResponse> {
  const response = await apiClient.post<ImpersonationTokenResponse>(
    `/admin/impersonate/${orgId}`
  );
  return response.data;
}

/**
 * Revoke the current impersonation session (best-effort).
 */
export async function revokeImpersonation(): Promise<void> {
  await apiClient.delete('/admin/impersonate/revoke');
}
