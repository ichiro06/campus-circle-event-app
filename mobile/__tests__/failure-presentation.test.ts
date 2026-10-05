import { describeFailure } from "../src/circles/failure-presentation";
import { ApiClientError } from "../src/api";
import { problemFailure, REQUEST_ID } from "../test-support/circles";

function failureOf(error: ApiClientError) {
  return error.failure;
}

describe("describeFailure", () => {
  const occurredAt = new Date(2026, 9, 5, 12, 0, 0);

  it("describes a network failure as offline", () => {
    expect(describeFailure({ kind: "network" })).toMatchObject({
      canRetry: true,
      kind: "offline",
      title: "オフラインです",
    });
  });

  it("describes a timeout", () => {
    expect(describeFailure({ kind: "timeout", timeoutMs: 10_000 })).toMatchObject({
      canRetry: true,
      kind: "timeout",
    });
  });

  it("describes a 404 without naming a cause and without a retry", () => {
    const presentation = describeFailure(failureOf(problemFailure(404, "NOT_FOUND")));

    expect(presentation).toMatchObject({
      canRetry: false,
      description: "現在このサークル情報を表示できません。",
      kind: "notFound",
      requestId: REQUEST_ID,
    });
  });

  it("describes a 429 with the time the user may retry", () => {
    const presentation = describeFailure(
      failureOf(problemFailure(429, "RATE_LIMITED", { retryAfterMs: 90_000 })),
      occurredAt,
    );

    expect(presentation.kind).toBe("rateLimited");
    expect(presentation.description).toContain("約90秒後（12:01以降）");
  });

  it("describes a 429 without Retry-After", () => {
    const presentation = describeFailure(failureOf(problemFailure(429, "RATE_LIMITED")));

    expect(presentation.description).not.toContain("約");
  });

  it("separates 503 from other server errors", () => {
    expect(describeFailure(failureOf(problemFailure(503, "X"))).kind).toBe("unavailable");
    expect(describeFailure(failureOf(problemFailure(500, "X"))).kind).toBe("serverError");
  });

  it("treats a gateway page without Problem Details as a server problem and shows no request ID", () => {
    const presentation = describeFailure({
      kind: "unexpectedResponse",
      httpStatus: 502,
    });

    expect(presentation.kind).toBe("serverError");
    expect(presentation.requestId).toBeUndefined();
  });

  it("never exposes the server title or detail", () => {
    const presentation = describeFailure(failureOf(problemFailure(500, "X")));

    expect(JSON.stringify(presentation)).not.toMatch(/internal|SELECT/);
  });

  it("explains INVALID_CURSOR and 422", () => {
    expect(describeFailure(failureOf(problemFailure(400, "INVALID_CURSOR")))).toMatchObject({
      canRetry: true,
      title: "続きを読み込めませんでした",
    });
    expect(describeFailure(failureOf(problemFailure(422, "VALIDATION_ERROR")))).toMatchObject({
      canRetry: false,
      kind: "invalidRequest",
    });
  });

  it("falls back for other 4xx and unexpected responses", () => {
    expect(describeFailure(failureOf(problemFailure(403, "FORBIDDEN"))).kind).toBe("unexpected");
    expect(describeFailure({ kind: "unexpectedResponse" }).kind).toBe("unexpected");
  });
});
