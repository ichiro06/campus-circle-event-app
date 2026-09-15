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
});
