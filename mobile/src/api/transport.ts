import { getApiBaseUrl, normalizeApiBaseUrl } from "@/config/environment";

import { ApiClientError } from "./errors";
import { parseProblemDetails } from "./problem-details";
import { serializeQueryParameters } from "./query-parameters";

export const DEFAULT_API_TIMEOUT_MS = 10_000;

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
  timeoutMs = DEFAULT_API_TIMEOUT_MS,
}: CreateApiTransportOptions = {}): ApiTransport {
  if (!Number.isFinite(timeoutMs) || timeoutMs <= 0) {
    throw new Error("API timeout must be a positive number");
  }

  const resolvedBaseUrl = baseUrl
    ? normalizeApiBaseUrl(baseUrl, { requireHttps: !__DEV__ })
    : getApiBaseUrl();

  return {
    async request<ResponseBody>(
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
          });
        }

        const problem = parseProblemDetails(body);

        if (!problem || problem.status !== response.status) {
          throw new ApiClientError({
            kind: "unexpectedResponse",
            httpStatus: response.status,
            contentType,
          });
        }

        throw new ApiClientError({
          kind: "problem",
          httpStatus: response.status,
          problem,
        });
      } finally {
        clearTimeout(timeoutId);
        options.signal?.removeEventListener("abort", handleCallerAbort);
      }
    },
  };
}
