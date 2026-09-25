import { normalizeApiBaseUrl } from "../src/config/environment";

describe("normalizeApiBaseUrl", () => {
  it("removes trailing slashes", () => {
    expect(normalizeApiBaseUrl(" https://api.example.com/// ")).toBe(
      "https://api.example.com",
    );
  });

  it("accepts the Android Emulator host address", () => {
    expect(normalizeApiBaseUrl("http://10.0.2.2:8000")).toBe(
      "http://10.0.2.2:8000",
    );
  });

  it("accepts an HTTPS origin", () => {
    expect(normalizeApiBaseUrl("https://api.example.com")).toBe(
      "https://api.example.com",
    );
  });

  it("rejects a missing value", () => {
    expect(() => normalizeApiBaseUrl(undefined)).toThrow(
      "EXPO_PUBLIC_API_BASE_URL is required",
    );
  });

  it("rejects unsupported protocols", () => {
    expect(() => normalizeApiBaseUrl("file:///tmp/api")).toThrow(
      "EXPO_PUBLIC_API_BASE_URL must use http or https",
    );
  });

  it("rejects credentials", () => {
    expect(() => normalizeApiBaseUrl("https://user:pass@api.example.com")).toThrow(
      "EXPO_PUBLIC_API_BASE_URL must not include credentials",
    );
  });

  it("rejects a query", () => {
    expect(() => normalizeApiBaseUrl("https://api.example.com?source=test")).toThrow(
      "EXPO_PUBLIC_API_BASE_URL must not include a query",
    );
    expect(() => normalizeApiBaseUrl("https://api.example.com?")).toThrow(
      "EXPO_PUBLIC_API_BASE_URL must not include a query",
    );
  });

  it("rejects a fragment", () => {
    expect(() => normalizeApiBaseUrl("https://api.example.com#fragment")).toThrow(
      "EXPO_PUBLIC_API_BASE_URL must not include a fragment",
    );
    expect(() => normalizeApiBaseUrl("https://api.example.com#")).toThrow(
      "EXPO_PUBLIC_API_BASE_URL must not include a fragment",
    );
  });

  it("rejects an API path", () => {
    expect(() => normalizeApiBaseUrl("https://api.example.com/api/v1")).toThrow(
      "EXPO_PUBLIC_API_BASE_URL must be an origin without an API path",
    );
  });

  it("rejects HTTP for release configuration", () => {
    expect(() =>
      normalizeApiBaseUrl("http://api.example.com", { requireHttps: true }),
    ).toThrow("EXPO_PUBLIC_API_BASE_URL must use https in release builds");
  });
});
