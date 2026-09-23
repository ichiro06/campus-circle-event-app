import { ApiClientError } from "../src/api/errors";
import {
  createApiTransport,
  DEFAULT_API_TIMEOUT_MS,
  type FetchImplementation,
} from "../src/api/transport";

const validProblem = {
  type: "about:blank",
  title: "Not Found",
  status: 404,
  detail: "The Circle was not found.",
  instance: "/api/v1/circles/00000000-0000-0000-0000-000000000001",
  code: "NOT_FOUND",
  requestId: "00000000-0000-0000-0000-000000000000",
};

interface MockResponseOptions {
  contentType?: string;
  jsonError?: unknown;
  status?: number;
}

function mockResponse(
  body: unknown,
  {
    contentType = "application/json",
    jsonError,
    status = 200,
  }: MockResponseOptions = {},
): Response {
  return {
    headers: {
      get: (name: string) =>
        name.toLowerCase() === "content-type" ? contentType : null,
    },
    json: jsonError
      ? jest.fn().mockRejectedValue(jsonError)
      : jest.fn().mockResolvedValue(body),
    ok: status >= 200 && status < 300,
    status,
  } as unknown as Response;
}

function createFetchMock(response: Response): jest.MockedFunction<FetchImplementation> {
  return jest.fn().mockResolvedValue(response) as jest.MockedFunction<FetchImplementation>;
}

function expectApiFailure(
  promise: Promise<unknown>,
  kind: ApiClientError["failure"]["kind"],
) {
  return expect(promise).rejects.toMatchObject({
    failure: { kind },
    name: "ApiClientError",
  });
}

describe("createApiTransport", () => {
  afterEach(() => {
    jest.useRealTimers();
  });

  it("returns a successful JSON response", async () => {
    const fetchMock = createFetchMock(mockResponse({ data: "ok" }));
    const transport = createApiTransport({
      baseUrl: "https://api.example.com",
      fetchImpl: fetchMock,
    });

    await expect(
      transport.request({ method: "GET", path: "/api/v1/health" }),
    ).resolves.toEqual({ data: "ok" });
  });

  it("serializes repeated query values without changing the cursor", async () => {
    const fetchMock = createFetchMock(mockResponse({ data: [] }));
    const transport = createApiTransport({
      baseUrl: "https://api.example.com",
      fetchImpl: fetchMock,
    });

    await transport.request({
      method: "GET",
      path: "/api/v1/circles",
      query: {
        weekday: ["1", "2"],
        cursor: "opaque+/=cursor",
      },
    });

    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      "https://api.example.com/api/v1/circles?weekday=1&weekday=2&cursor=opaque%2B%2F%3Dcursor",
    );
  });

  it("classifies a valid HTTP Problem", async () => {
    const transport = createApiTransport({
      baseUrl: "https://api.example.com",
      fetchImpl: createFetchMock(
        mockResponse(validProblem, {
          contentType: "application/problem+json; charset=utf-8",
          status: 404,
        }),
      ),
    });

    await expect(
      transport.request({ method: "GET", path: "/api/v1/circles/id" }),
    ).rejects.toMatchObject({
      failure: {
        httpStatus: 404,
        kind: "problem",
        problem: {
          code: "NOT_FOUND",
          requestId: "00000000-0000-0000-0000-000000000000",
        },
      },
    });
  });

  it.each([
    {
      name: "status mismatch",
      response: mockResponse({ ...validProblem, status: 422 }, {
        contentType: "application/problem+json",
        status: 404,
      }),
    },
    {
      name: "broken Problem",
      response: mockResponse({ code: "NOT_FOUND" }, {
        contentType: "application/problem+json",
        status: 404,
      }),
    },
    {
      name: "non-Problem JSON error",
      response: mockResponse({ error: "not found" }, {
        contentType: "application/json",
        status: 404,
      }),
    },
    {
      name: "non-JSON error",
      response: mockResponse("not found", {
        contentType: "text/plain",
        status: 404,
      }),
    },
    {
      name: "non-JSON success",
      response: mockResponse("ok", {
        contentType: "text/plain",
        status: 200,
      }),
    },
    {
      name: "invalid JSON",
      response: mockResponse(undefined, {
        contentType: "application/problem+json",
        jsonError: new SyntaxError("invalid JSON"),
        status: 404,
      }),
    },
  ])("classifies $name as unexpectedResponse", async ({ response }) => {
    const transport = createApiTransport({
      baseUrl: "https://api.example.com",
      fetchImpl: createFetchMock(response),
    });

    await expectApiFailure(
      transport.request({ method: "GET", path: "/api/v1/circles/id" }),
      "unexpectedResponse",
    );
  });

  it("classifies a fetch failure as network", async () => {
    const fetchMock = jest
      .fn()
      .mockRejectedValue(new TypeError("Network request failed")) as jest.MockedFunction<FetchImplementation>;
    const transport = createApiTransport({
      baseUrl: "https://api.example.com",
      fetchImpl: fetchMock,
    });

    await expectApiFailure(
      transport.request({ method: "GET", path: "/api/v1/circles" }),
      "network",
    );
  });

  it("distinguishes the project timeout and clears the timer", async () => {
    jest.useFakeTimers();
    let requestSignal: AbortSignal | undefined;
    const fetchMock = jest.fn(
      (_input: Parameters<FetchImplementation>[0], init?: RequestInit) =>
        new Promise<Response>((_resolve, reject) => {
          requestSignal = init?.signal ?? undefined;
          requestSignal?.addEventListener("abort", () => reject(new Error("aborted")));
        }),
    ) as jest.MockedFunction<FetchImplementation>;
    const transport = createApiTransport({
      baseUrl: "https://api.example.com",
      fetchImpl: fetchMock,
    });
    const request = transport.request({
      method: "GET",
      path: "/api/v1/circles",
    });
    const expectation = expectApiFailure(request, "timeout");

    await jest.advanceTimersByTimeAsync(DEFAULT_API_TIMEOUT_MS);
    await expectation;
    expect(requestSignal?.aborted).toBe(true);
    expect(jest.getTimerCount()).toBe(0);
  });

  it("distinguishes caller cancellation from timeout", async () => {
    jest.useFakeTimers();
    const callerController = new AbortController();
    const fetchMock = jest.fn(
      (_input: Parameters<FetchImplementation>[0], init?: RequestInit) =>
        new Promise<Response>((_resolve, reject) => {
          init?.signal?.addEventListener("abort", () => reject(new Error("aborted")));
        }),
    ) as jest.MockedFunction<FetchImplementation>;
    const transport = createApiTransport({
      baseUrl: "https://api.example.com",
      fetchImpl: fetchMock,
    });
    const request = transport.request({
      method: "GET",
      path: "/api/v1/circles",
      signal: callerController.signal,
    });
    const expectation = expectApiFailure(request, "cancelled");

    callerController.abort();
    await expectation;
    expect(jest.getTimerCount()).toBe(0);
  });

  it("cleans up the timer after a successful request", async () => {
    jest.useFakeTimers();
    let requestSignal: AbortSignal | undefined;
    const fetchMock = jest.fn(
      async (_input: Parameters<FetchImplementation>[0], init?: RequestInit) => {
        requestSignal = init?.signal ?? undefined;
        return mockResponse({ data: [] });
      },
    ) as jest.MockedFunction<FetchImplementation>;
    const transport = createApiTransport({
      baseUrl: "https://api.example.com",
      fetchImpl: fetchMock,
    });

    await transport.request({ method: "GET", path: "/api/v1/circles" });
    await jest.advanceTimersByTimeAsync(DEFAULT_API_TIMEOUT_MS);

    expect(requestSignal?.aborted).toBe(false);
    expect(jest.getTimerCount()).toBe(0);
  });

  it("removes the caller abort listener after completion", async () => {
    const callerController = new AbortController();
    const addEventListener = jest.spyOn(
      callerController.signal,
      "addEventListener",
    );
    const removeEventListener = jest.spyOn(
      callerController.signal,
      "removeEventListener",
    );
    const transport = createApiTransport({
      baseUrl: "https://api.example.com",
      fetchImpl: createFetchMock(mockResponse({ data: [] })),
    });

    await transport.request({
      method: "GET",
      path: "/api/v1/circles",
      signal: callerController.signal,
    });

    const abortListener = addEventListener.mock.calls.find(
      ([eventName]) => eventName === "abort",
    )?.[1];
    expect(abortListener).toEqual(expect.any(Function));
    expect(removeEventListener).toHaveBeenCalledWith("abort", abortListener);
  });

  it("adds safe custom headers without Authorization", async () => {
    const fetchMock = createFetchMock(mockResponse({ data: [] }));
    const transport = createApiTransport({
      baseUrl: "https://api.example.com",
      fetchImpl: fetchMock,
    });

    await transport.request({
      headers: { "X-Client-Version": "1.0.0" },
      method: "GET",
      path: "/api/v1/circles",
    });

    expect(fetchMock.mock.calls[0]?.[1]?.headers).toMatchObject({
      "X-Client-Version": "1.0.0",
    });
    expect(fetchMock.mock.calls[0]?.[1]?.headers).not.toHaveProperty(
      "Authorization",
    );
  });

  it("injects a Bearer token from the token provider", async () => {
    const fetchMock = createFetchMock(mockResponse({ data: [] }));
    const transport = createApiTransport({
      accessTokenProvider: async () => "test-token",
      baseUrl: "https://api.example.com",
      fetchImpl: fetchMock,
    });

    await transport.request({ method: "GET", path: "/api/v1/circles" });

    expect(fetchMock.mock.calls[0]?.[1]?.headers).toMatchObject({
      Authorization: "Bearer test-token",
    });
  });

  it("rejects a caller-supplied Authorization header", async () => {
    const fetchMock = createFetchMock(mockResponse({ data: [] }));
    const transport = createApiTransport({
      baseUrl: "https://api.example.com",
      fetchImpl: fetchMock,
    });

    await expect(
      transport.request({
        headers: { authorization: "Bearer caller-token" },
        method: "GET",
        path: "/api/v1/circles",
      }),
    ).rejects.toThrow("Authorization is managed by the API transport");
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
