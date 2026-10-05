import { ApiClientError } from "../src/api/errors";
import {
  createApiTransport,
  parseRetryAfterMs,
  type FetchImplementation,
} from "../src/api/transport";

const validProblem = (status: number) => ({
  type: "about:blank",
  title: "title",
  status,
  detail: "detail",
  instance: "/api/v1/circles",
  code: "SOME_CODE",
  requestId: "00000000-0000-0000-0000-000000000000",
});

interface ResponseOptions {
  contentType?: string;
  headers?: Record<string, string>;
  status?: number;
}

function jsonResponse(
  body: unknown,
  { contentType = "application/json", headers = {}, status = 200 }: ResponseOptions = {},
): Response {
  const allHeaders: Record<string, string> = {
    "content-type": contentType,
    ...headers,
  };

  return {
    headers: { get: (name: string) => allHeaders[name.toLowerCase()] ?? null },
    json: jest.fn().mockResolvedValue(body),
    ok: status >= 200 && status < 300,
    status,
  } as unknown as Response;
}

function problemResponse(status: number, headers: Record<string, string> = {}) {
  return jsonResponse(validProblem(status), {
    contentType: "application/problem+json",
    headers,
    status,
  });
}

function createTransport(
  fetchMock: jest.MockedFunction<FetchImplementation>,
  options: { random?: () => number; timeoutMs?: number } = {},
) {
  return createApiTransport({
    baseUrl: "https://api.example.com",
    fetchImpl: fetchMock,
    random: options.random ?? (() => 0),
    timeoutMs: options.timeoutMs,
  });
}

function mockFetch(...results: (Response | Error)[]) {
  const fetchMock = jest.fn() as jest.MockedFunction<FetchImplementation>;

  for (const result of results) {
    if (result instanceof Error) {
      fetchMock.mockRejectedValueOnce(result);
    } else {
      fetchMock.mockResolvedValueOnce(result);
    }
  }

  return fetchMock;
}

async function advance(ms: number) {
  await jest.advanceTimersByTimeAsync(ms);
}

const request = { method: "GET", path: "/api/v1/circles" } as const;

describe("GET retry", () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it.each([429, 502, 503, 504])("retries a %i problem and then succeeds", async (status) => {
    const fetchMock = mockFetch(
      problemResponse(status),
      jsonResponse({ data: "ok" }),
    );
    const pending = createTransport(fetchMock).request(request);

    await advance(500);

    await expect(pending).resolves.toEqual({ data: "ok" });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it.each([502, 503, 504])(
    "retries a non-JSON %i gateway response",
    async (status) => {
      const fetchMock = mockFetch(
        jsonResponse("bad gateway", { contentType: "text/html", status }),
        jsonResponse({ data: "ok" }),
      );
      const pending = createTransport(fetchMock).request(request);

      await advance(500);

      await expect(pending).resolves.toEqual({ data: "ok" });
      expect(fetchMock).toHaveBeenCalledTimes(2);
    },
  );

  it("retries a network error", async () => {
    const fetchMock = mockFetch(
      new TypeError("Network request failed"),
      jsonResponse({ data: "ok" }),
    );
    const pending = createTransport(fetchMock).request(request);

    await advance(500);

    await expect(pending).resolves.toEqual({ data: "ok" });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("retries a timeout, using a fresh 10 second window per attempt", async () => {
    const fetchMock = jest.fn() as jest.MockedFunction<FetchImplementation>;
    fetchMock.mockImplementationOnce(() => new Promise<Response>(() => {}));
    fetchMock.mockResolvedValueOnce(jsonResponse({ data: "ok" }));
    const pending = createTransport(fetchMock).request(request);

    await advance(10_000);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    await advance(500);

    await expect(pending).resolves.toEqual({ data: "ok" });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it.each([400, 401, 403, 404, 409, 422])(
    "does not retry a %i problem",
    async (status) => {
      const fetchMock = mockFetch(problemResponse(status));

      await expect(createTransport(fetchMock).request(request)).rejects.toMatchObject({
        failure: { kind: "problem", httpStatus: status },
      });
      expect(fetchMock).toHaveBeenCalledTimes(1);
    },
  );

  it("does not retry a 500 problem", async () => {
    const fetchMock = mockFetch(problemResponse(500));

    await expect(createTransport(fetchMock).request(request)).rejects.toMatchObject({
      failure: { kind: "problem", httpStatus: 500 },
    });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("does not retry a malformed 200 body", async () => {
    const fetchMock = mockFetch(
      jsonResponse("ok", { contentType: "text/plain", status: 200 }),
    );

    await expect(createTransport(fetchMock).request(request)).rejects.toMatchObject({
      failure: { kind: "unexpectedResponse" },
    });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("retries at most twice, waiting about 0.5s then 1.5s, and returns the last error", async () => {
    const fetchMock = mockFetch(
      problemResponse(503),
      problemResponse(503),
      problemResponse(503),
      jsonResponse({ data: "never reached" }),
    );
    const pending = createTransport(fetchMock).request(request);
    const settled = pending.catch((error: unknown) => error);

    await advance(0);
    expect(fetchMock).toHaveBeenCalledTimes(1);

    await advance(499);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    await advance(1);
    expect(fetchMock).toHaveBeenCalledTimes(2);

    await advance(1_499);
    expect(fetchMock).toHaveBeenCalledTimes(2);
    await advance(1);
    expect(fetchMock).toHaveBeenCalledTimes(3);

    const error = await settled;
    await advance(10_000);

    expect(error).toBeInstanceOf(ApiClientError);
    expect(error).toMatchObject({ failure: { kind: "problem", httpStatus: 503 } });
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it("adds jitter on top of the base delay", async () => {
    const fetchMock = mockFetch(problemResponse(503), jsonResponse({ data: "ok" }));
    const pending = createTransport(fetchMock, { random: () => 0.8 }).request(request);

    await advance(0);
    // base 500ms + 0.8 * 25% jitter = 600ms
    await advance(599);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    await advance(1);

    await expect(pending).resolves.toEqual({ data: "ok" });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it.each([
    ["3", 3_000],
    ["30", 30_000],
    ["120", 120_000],
  ])("waits the full Retry-After of %s seconds before retrying", async (value, waitMs) => {
    const fetchMock = mockFetch(
      problemResponse(429, { "retry-after": value }),
      jsonResponse({ data: "ok" }),
    );
    const pending = createTransport(fetchMock).request(request);

    await advance(waitMs - 1);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    await advance(1);

    await expect(pending).resolves.toEqual({ data: "ok" });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("uses an HTTP-date Retry-After as the retry wait", async () => {
    jest.setSystemTime(Date.parse("2026-10-05T00:00:00Z"));
    const fetchMock = mockFetch(
      problemResponse(503, { "retry-after": "Mon, 05 Oct 2026 00:00:45 GMT" }),
      jsonResponse({ data: "ok" }),
    );
    const pending = createTransport(fetchMock).request(request);

    await advance(44_999);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    await advance(1);

    await expect(pending).resolves.toEqual({ data: "ok" });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("keeps the two-retry limit when Retry-After is used", async () => {
    const fetchMock = mockFetch(
      problemResponse(429, { "retry-after": "60" }),
      problemResponse(429, { "retry-after": "120" }),
      problemResponse(429, { "retry-after": "180" }),
      jsonResponse({ data: "never reached" }),
    );
    const settled = createTransport(fetchMock)
      .request(request)
      .catch((error: unknown) => error);

    await advance(60_000);
    expect(fetchMock).toHaveBeenCalledTimes(2);
    await advance(120_000);
    expect(fetchMock).toHaveBeenCalledTimes(3);

    const error = await settled;
    await advance(300_000);

    expect(error).toMatchObject({
      failure: { kind: "problem", httpStatus: 429, retryAfterMs: 180_000 },
    });
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it("stops waiting when the caller cancels during a long Retry-After", async () => {
    const fetchMock = mockFetch(
      problemResponse(429, { "retry-after": "120" }),
      jsonResponse({ data: "ok" }),
    );
    const controller = new AbortController();
    const settled = createTransport(fetchMock)
      .request({ ...request, signal: controller.signal })
      .catch((error: unknown) => error);

    await advance(30_000);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    controller.abort();

    await expect(settled).resolves.toMatchObject({ failure: { kind: "cancelled" } });
    expect(jest.getTimerCount()).toBe(0);
    await advance(300_000);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("stops waiting when the caller cancels during the backoff", async () => {
    const fetchMock = mockFetch(problemResponse(503), jsonResponse({ data: "ok" }));
    const controller = new AbortController();
    const pending = createTransport(fetchMock).request({
      ...request,
      signal: controller.signal,
    });
    const settled = pending.catch((error: unknown) => error);

    await advance(100);
    controller.abort();

    await expect(settled).resolves.toMatchObject({ failure: { kind: "cancelled" } });
    await advance(5_000);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("leaves no pending timers once the retries are exhausted", async () => {
    const fetchMock = mockFetch(
      problemResponse(503),
      problemResponse(503),
      problemResponse(503),
    );
    const settled = createTransport(fetchMock)
      .request(request)
      .catch((error: unknown) => error);

    await advance(2_000);
    await settled;

    expect(jest.getTimerCount()).toBe(0);
  });
});

describe("parseRetryAfterMs", () => {
  it("parses delta-seconds", () => {
    expect(parseRetryAfterMs("2")).toBe(2_000);
    expect(parseRetryAfterMs(" 0 ")).toBe(0);
  });

  it("parses an HTTP-date relative to now", () => {
    const now = Date.parse("2026-10-05T00:00:00Z");

    expect(parseRetryAfterMs("Mon, 05 Oct 2026 00:00:05 GMT", now)).toBe(5_000);
    expect(parseRetryAfterMs("Mon, 05 Oct 2026 00:00:00 GMT", now + 10_000)).toBe(0);
  });

  it("ignores missing or malformed values", () => {
    expect(parseRetryAfterMs(null)).toBeUndefined();
    expect(parseRetryAfterMs("")).toBeUndefined();
    expect(parseRetryAfterMs("soon")).toBeUndefined();
  });
});
