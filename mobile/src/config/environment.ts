const SUPPORTED_PROTOCOLS = new Set(["http:", "https:"]);

export function normalizeApiBaseUrl(value: string | undefined): string {
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

  return candidate.replace(/\/+$/, "");
}

export function getApiBaseUrl(): string {
  return normalizeApiBaseUrl(process.env.EXPO_PUBLIC_API_BASE_URL);
}
