import { getApiBaseUrl, normalizeApiBaseUrl } from "@/config/environment";

import { ApiClientError, type ApiFailure } from "./errors";
import { parseProblemDetails } from "./problem-details";
import { serializeQueryParameters } from "./query-parameters";

export const DEFAULT_API_TIMEOUT_MS = 10_000;

// docs/screen-flow.md 6: GET retries at most twice, after about 0.5s and 1.5s plus jitter.
export const DEFAULT_RETRY_DELAYS_MS: readonly number[] = [500, 1_500];
export const RETRY_JITTER_RATIO = 0.25;
// A Retry-After longer than this is surfaced to the caller instead of being waited on silently.
export const MAX_AUTOMATIC_RETRY_WAIT_MS = 10_000;
export const RETRYABLE_HTTP_STATUSES: readonly number[] = [429, 502, 503, 504];

export type AccessTokenProvider = () => Promise<string | null>;
export type FetchImplementation = typeof fetch;

export interface ApiRequestOptions {
  method: "GET";
  path: string;
  query?: object;
  headers?: Readonly<Record<string, string>>;
  signal?: AbortSignal;
}

export interface ApiTransport {
  request<ResponseBody>(options: ApiRequestOptions): Promise<ResponseBody>;
}

export interface CreateApiTransportOptions {
  accessTokenProvider?: AccessTokenProvider;
  baseUrl?: string;
  fetchImpl?: FetchImplementation;
  /** Jitter source in [0, 1). Injectable so tests stay deterministic. */
  random?: () => number;
  /** Delays before each GET retry. The array length is the maximum retry count. */
  retryDelaysMs?: readonly number[];
  timeoutMs?: number;
}

type AbortSource = "cancelled" | "timeout";

function getContentType(response: Response): string | undefined {
  return response.headers.get("content-type")?.split(";", 1)[0]?.trim().toLowerCase();
}

function isJsonContentType(contentType: string | undefined): boolean {
  return (
    contentType === "application/json" ||
    contentType?.endsWith("+json") === true
  );
}

export function parseRetryAfterMs(
  value: string | null | undefined,
  now: number = Date.now(),
): number | undefined {
  const candidate = value?.trim();

  if (!candidate) {
    return undefined;
  }

  if (/^\d+$/u.test(candidate)) {
    return Number(candidate) * 1_000;
  }

  const date = Date.parse(candidate);

  return Number.isNaN(date) ? undefined : Math.max(0, date - now);
}

function getRetryAfterMs(response: Response): number | undefined {
  return parseRetryAfterMs(response.headers.get("retry-after"));
}

function isRetryableFailure(failure: ApiFailure): boolean {
  switch (failure.kind) {
    case "network":
    case "timeout":
      return true;
    case "problem":
      return RETRYABLE_HTTP_STATUSES.includes(failure.httpStatus);
    case "unexpectedResponse":
      return (
        failure.httpStatus !== undefined &&
        RETRYABLE_HTTP_STATUSES.includes(failure.httpStatus)
      );
    case "cancelled":
      return false;
  }
}

function getRetryWaitMs(
  failure: ApiFailure,
  baseDelayMs: number,
  random: () => number,
): number | undefined {
  const retryAfterMs =
    failure.kind === "problem" || failure.kind === "unexpectedResponse"
      ? failure.retryAfterMs
      : undefined;

  if (retryAfterMs !== undefined) {
    return retryAfterMs > MAX_AUTOMATIC_RETRY_WAIT_MS ? undefined : retryAfterMs;
  }

  return Math.round(baseDelayMs * (1 + random() * RETRY_JITTER_RATIO));
}

function waitBeforeRetry(waitMs: number, signal?: AbortSignal): Promise<void> {
  return new Promise<void>((resolve, reject) => {
    if (signal?.aborted) {
      reject(new ApiClientError({ kind: "cancelled" }));
      return;
    }

    const handleAbort = () => {
      clearTimeout(timeoutId);
      reject(new ApiClientError({ kind: "cancelled" }));
    };
    const timeoutId = setTimeout(() => {
      signal?.removeEventListener("abort", handleAbort);
      resolve();
    }, waitMs);

    signal?.addEventListener("abort", handleAbort, { once: true });
  });
}

function getAbortError(
  abortSource: AbortSource,
  timeoutMs: number,
): ApiClientError {
  if (abortSource === "timeout") {
    return new ApiClientError({ kind: "timeout", timeoutMs });
  }

  return new ApiClientError({ kind: "cancelled" });
}

function buildHeaders(
  customHeaders: Readonly<Record<string, string>> | undefined,
  accessToken: string | null,
): Record<string, string> {
  const headers: Record<string, string> = {
    Accept: "application/json, application/problem+json",
  };

  for (const [name, value] of Object.entries(customHeaders ?? {})) {
    const normalizedName = name.toLowerCase();

    if (normalizedName === "authorization") {
      throw new Error("Authorization is managed by the API transport");
    }

    if (normalizedName === "accept") {
      throw new Error("Accept is managed by the API transport");
    }

    headers[name] = value;
  }

  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }

  return headers;
}

function buildUrl(baseUrl: string, options: ApiRequestOptions): string {
  if (!options.path.startsWith("/") || options.path.startsWith("//")) {
    throw new Error("API request path must be an absolute path without an origin");
  }

  const queryString = serializeQueryParameters(options.query);
  return `${baseUrl}${options.path}${queryString ? `?${queryString}` : ""}`;
}

async function resolveAccessToken(
  accessTokenProvider: AccessTokenProvider,
): Promise<string | null> {
  try {
    return await accessTokenProvider();
  } catch (cause) {
    throw new ApiClientError({ kind: "network", cause });
  }
}

export function createApiTransport({
  accessTokenProvider,
  baseUrl,
  fetchImpl = fetch,
  random = Math.random,
  retryDelaysMs = DEFAULT_RETRY_DELAYS_MS,
  timeoutMs = DEFAULT_API_TIMEOUT_MS,
}: CreateApiTransportOptions = {}): ApiTransport {
  if (!Number.isFinite(timeoutMs) || timeoutMs <= 0) {
    throw new Error("API timeout must be a positive number");
  }

  const resolvedBaseUrl = baseUrl
    ? normalizeApiBaseUrl(baseUrl, { requireHttps: !__DEV__ })
    : getApiBaseUrl();

  async function requestOnce<ResponseBody>(
    options: ApiRequestOptions,
  ): Promise<ResponseBody> {
    if (options.signal?.aborted) {
      throw getAbortError("cancelled", timeoutMs);
    }

    const controller = new AbortController();
    let abortSource: AbortSource | undefined;
    let rejectForAbort: (error: ApiClientError) => void = () => {};
    const abortPromise = new Promise<never>((_resolve, reject) => {
      rejectForAbort = reject;
    });
    const raceWithAbort = <Value>(promise: Promise<Value>) =>
      Promise.race([promise, abortPromise]);

    const abort = (source: AbortSource) => {
      if (abortSource) {
        return;
      }

      abortSource = source;
      rejectForAbort(getAbortError(source, timeoutMs));
      controller.abort();
    };

    const handleCallerAbort = () => abort("cancelled");

    options.signal?.addEventListener("abort", handleCallerAbort, {
      once: true,
    });

    const timeoutId = setTimeout(() => abort("timeout"), timeoutMs);

    try {
      const accessToken = accessTokenProvider
        ? await raceWithAbort(resolveAccessToken(accessTokenProvider))
        : null;

      if (abortSource) {
        throw getAbortError(abortSource, timeoutMs);
      }

      const url = buildUrl(resolvedBaseUrl, options);
      const headers = buildHeaders(options.headers, accessToken);

      let response: Response;

      try {
        response = await raceWithAbort(
          fetchImpl(url, {
            headers,
            method: options.method,
            signal: controller.signal,
          }),
        );
      } catch (cause) {
        if (abortSource) {
          throw getAbortError(abortSource, timeoutMs);
        }

        throw new ApiClientError({ kind: "network", cause });
      }

      const contentType = getContentType(response);

      if (!isJsonContentType(contentType)) {
        throw new ApiClientError({
          kind: "unexpectedResponse",
          httpStatus: response.status,
          contentType,
          retryAfterMs: getRetryAfterMs(response),
        });
      }

      let body: unknown;

      try {
        body = await raceWithAbort(response.json());
      } catch {
        if (abortSource) {
          throw getAbortError(abortSource, timeoutMs);
        }

        throw new ApiClientError({
          kind: "unexpectedResponse",
          httpStatus: response.status,
          contentType,
          retryAfterMs: getRetryAfterMs(response),
        });
      }

      if (abortSource) {
        throw getAbortError(abortSource, timeoutMs);
      }

      if (response.ok) {
        return body as ResponseBody;
      }

      if (contentType !== "application/problem+json") {
        throw new ApiClientError({
          kind: "unexpectedResponse",
          httpStatus: response.status,
          contentType,
          retryAfterMs: getRetryAfterMs(response),
        });
      }

      const problem = parseProblemDetails(body);

      if (!problem || problem.status !== response.status) {
        throw new ApiClientError({
          kind: "unexpectedResponse",
          httpStatus: response.status,
          contentType,
          retryAfterMs: getRetryAfterMs(response),
        });
      }

      throw new ApiClientError({
        kind: "problem",
        httpStatus: response.status,
        problem,
        retryAfterMs: getRetryAfterMs(response),
      });
    } finally {
      clearTimeout(timeoutId);
      options.signal?.removeEventListener("abort", handleCallerAbort);
    }
  }

  return {
    async request<ResponseBody>(
      options: ApiRequestOptions,
    ): Promise<ResponseBody> {
      for (let attempt = 0; ; attempt += 1) {
        try {
          return await requestOnce<ResponseBody>(options);
        } catch (error) {
          const baseDelayMs = retryDelaysMs[attempt];

          if (
            options.method !== "GET" ||
            baseDelayMs === undefined ||
            !(error instanceof ApiClientError) ||
            !isRetryableFailure(error.failure)
          ) {
            throw error;
          }

          const waitMs = getRetryWaitMs(error.failure, baseDelayMs, random);

          if (waitMs === undefined) {
            throw error;
          }

          await waitBeforeRetry(waitMs, options.signal);
        }
      }
    },
  };
}
