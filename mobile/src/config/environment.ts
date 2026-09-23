const SUPPORTED_PROTOCOLS = new Set(["http:", "https:"]);

export interface ApiBaseUrlOptions {
  requireHttps?: boolean;
}

export function normalizeApiBaseUrl(
  value: string | undefined,
  { requireHttps = false }: ApiBaseUrlOptions = {},
): string {
  const candidate = value?.trim();

  if (!candidate) {
    throw new Error("EXPO_PUBLIC_API_BASE_URL is required");
  }

  let parsed: URL;

  try {
    parsed = new URL(candidate);
  } catch {
    throw new Error("EXPO_PUBLIC_API_BASE_URL must be an absolute URL");
  }

  if (!SUPPORTED_PROTOCOLS.has(parsed.protocol)) {
    throw new Error("EXPO_PUBLIC_API_BASE_URL must use http or https");
  }

  if (requireHttps && parsed.protocol !== "https:") {
    throw new Error("EXPO_PUBLIC_API_BASE_URL must use https in release builds");
  }

  if (parsed.username || parsed.password) {
    throw new Error("EXPO_PUBLIC_API_BASE_URL must not include credentials");
  }

  if (parsed.search || candidate.includes("?")) {
    throw new Error("EXPO_PUBLIC_API_BASE_URL must not include a query");
  }

  if (parsed.hash || candidate.includes("#")) {
    throw new Error("EXPO_PUBLIC_API_BASE_URL must not include a fragment");
  }

  if (!/^\/+$/u.test(parsed.pathname)) {
    throw new Error("EXPO_PUBLIC_API_BASE_URL must be an origin without an API path");
  }

  return parsed.origin;
}

export function getApiBaseUrl(): string {
  return normalizeApiBaseUrl(process.env.EXPO_PUBLIC_API_BASE_URL, {
    requireHttps: !__DEV__,
  });
}
