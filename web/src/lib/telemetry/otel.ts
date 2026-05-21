/**
 * otel.ts — Lightweight web telemetry module for Context-OS.
 *
 * Sends OTLP-compatible span JSON to a configured endpoint via fetch().
 * No external OpenTelemetry packages required — uses fetch() directly.
 * All errors are silently caught; telemetry never throws.
 *
 * Activation: set VITE_OTEL_EXPORTER_OTLP_ENDPOINT in your environment.
 * If the env var is unset, all functions are no-ops.
 */

import type { QueryClient } from '@tanstack/react-query';

export interface OtelConfig {
  /** OTLP HTTP endpoint, e.g. http://localhost:4318 */
  endpoint: string | undefined;
  /** Clerk tenant/org ID injected into every span */
  tenantId: string | null;
}

// ── Module-level singleton state ─────────────────────────────────────────────

let _endpoint: string | undefined = undefined;
let _tenantId: string | null = null;
let _queryUnsubscribe: (() => void) | null = null;

// ── Span utilities ────────────────────────────────────────────────────────────

/** Produce a simple 16-char hex trace/span ID */
function randomHex(bytes: number): string {
  const arr = new Uint8Array(bytes);
  crypto.getRandomValues(arr);
  return Array.from(arr, (b) => b.toString(16).padStart(2, '0')).join('');
}

interface SpanAttributes {
  [key: string]: string | number | boolean;
}

interface OtlpSpan {
  traceId: string;
  spanId: string;
  name: string;
  kind: number; // 0=INTERNAL, 1=SERVER, 2=CLIENT
  startTimeUnixNano: string;
  endTimeUnixNano: string;
  attributes: Array<{ key: string; value: { stringValue?: string; intValue?: string; doubleValue?: number } }>;
  status: { code: number };
}

function buildSpan(
  name: string,
  startMs: number,
  endMs: number,
  attrs: SpanAttributes
): OtlpSpan {
  const allAttrs: SpanAttributes = {
    'context_os.tenant_id': _tenantId ?? 'unknown',
    ...attrs,
  };

  return {
    traceId: randomHex(16),
    spanId: randomHex(8),
    name,
    kind: 0,
    startTimeUnixNano: String(startMs * 1_000_000),
    endTimeUnixNano: String(endMs * 1_000_000),
    attributes: Object.entries(allAttrs).map(([key, value]) => {
      if (typeof value === 'number') {
        return Number.isInteger(value)
          ? { key, value: { intValue: String(value) } }
          : { key, value: { doubleValue: value } };
      }
      return { key, value: { stringValue: String(value) } };
    }),
    status: { code: 1 }, // OK
  };
}

/** Fire-and-forget OTLP span export */
function exportSpan(span: OtlpSpan): void {
  if (!_endpoint) return;

  const body = JSON.stringify({
    resourceSpans: [
      {
        resource: {
          attributes: [
            { key: 'service.name', value: { stringValue: 'context-os-web' } },
            { key: 'context_os.tenant_id', value: { stringValue: _tenantId ?? 'unknown' } },
          ],
        },
        scopeSpans: [
          {
            scope: { name: 'context-os-web', version: '1.0.0' },
            spans: [span],
          },
        ],
      },
    ],
  });

  fetch(`${_endpoint}/v1/traces`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body,
    keepalive: true,
  }).catch(() => {
    // Silent — telemetry must never interrupt the user experience
  });
}

// ── Public API ────────────────────────────────────────────────────────────────

/**
 * Initialize the OTEL module. Call once at app startup.
 * If `config.endpoint` is undefined, all subsequent calls are no-ops.
 */
export function initOtel(config: OtelConfig): void {
  _endpoint = config.endpoint;
  _tenantId = config.tenantId;
}

/**
 * Update the tenantId after Clerk authentication resolves.
 * Useful when the tenant is not known at initOtel time.
 */
export function initOtelWithTenantId(tenantId: string): void {
  _tenantId = tenantId;
  if (!_endpoint) {
    _endpoint = import.meta.env['VITE_OTEL_EXPORTER_OTLP_ENDPOINT'] as string | undefined;
  }
}

/**
 * Track a route transition span.
 * Call from a React effect or router NavigationContext subscriber.
 */
export function trackRouteTransition(from: string, to: string): void {
  if (!_endpoint) return;
  try {
    const now = Date.now();
    const span = buildSpan('navigation.route_transition', now - 1, now, {
      'view.from': from,
      'view.to': to,
      timestamp: new Date(now).toISOString(),
    });
    exportSpan(span);
  } catch {
    // Silent
  }
}

/**
 * Instrument a TanStack QueryClient — subscribes to cache events and
 * emits a span for each successful query fetch with duration and queryKey.
 *
 * Safe to call multiple times (unsubscribes previous listener first).
 */
export function instrumentQueryClient(queryClient: QueryClient): void {
  if (!_endpoint) return;

  try {
    // Unsubscribe previous listener if any
    if (_queryUnsubscribe) {
      _queryUnsubscribe();
      _queryUnsubscribe = null;
    }

    // Track in-flight query start times keyed by query hash
    const startTimes = new Map<string, number>();

    const cache = queryClient.getQueryCache();

    _queryUnsubscribe = cache.subscribe((event) => {
      try {
        if (!_endpoint) return;

        const queryHash = event.query.queryHash;

        if (event.type === 'observerResultsUpdated') {
          const state = event.query.state;

          if (state.fetchStatus === 'fetching' && !startTimes.has(queryHash)) {
            startTimes.set(queryHash, Date.now());
          }

          if (state.fetchStatus === 'idle' && state.status === 'success') {
            const startMs = startTimes.get(queryHash);
            if (startMs !== undefined) {
              const endMs = Date.now();
              startTimes.delete(queryHash);

              const keyJson = JSON.stringify(event.query.queryKey);
              const span = buildSpan('query.fetch_success', startMs, endMs, {
                'query.key': keyJson,
                'query.duration_ms': endMs - startMs,
                'query.status': 'success',
              });
              exportSpan(span);
            }
          }

          if (state.fetchStatus === 'idle' && state.status === 'error') {
            startTimes.delete(queryHash);
          }
        }
      } catch {
        // Silent
      }
    });
  } catch {
    // Silent
  }
}

/**
 * Track a custom named span with arbitrary attributes.
 * Useful for Sigma render frame timing, custom interactions, etc.
 */
export function trackSpan(name: string, attributes: Record<string, string | number>): void {
  if (!_endpoint) return;
  try {
    const now = Date.now();
    const durationMs =
      typeof attributes['duration_ms'] === 'number' ? (attributes['duration_ms'] as number) : 0;
    const startMs = now - durationMs;
    const span = buildSpan(name, startMs, now, attributes);
    exportSpan(span);
  } catch {
    // Silent
  }
}

// ── Singleton export ──────────────────────────────────────────────────────────

export const otel = {
  init: initOtel,
  initWithTenantId: initOtelWithTenantId,
  trackRouteTransition,
  instrumentQueryClient,
  trackSpan,
} as const;

export default otel;
