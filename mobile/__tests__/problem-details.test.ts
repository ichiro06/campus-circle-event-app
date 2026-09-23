import { parseProblemDetails } from "../src/api/problem-details";

const validProblem = {
  type: "about:blank",
  title: "Unprocessable Content",
  status: 422,
  detail: "The request contains invalid fields.",
  instance: "/api/v1/circles",
  code: "VALIDATION_ERROR",
  requestId: "00000000-0000-0000-0000-000000000000",
  errors: [{ field: "q", code: "too_short" }],
};

describe("parseProblemDetails", () => {
  it("accepts the formal about:blank problem and preserves stable fields", () => {
    expect(parseProblemDetails(validProblem)).toMatchObject({
      type: "about:blank",
      code: "VALIDATION_ERROR",
      requestId: "00000000-0000-0000-0000-000000000000",
      errors: [{ field: "q", code: "too_short" }],
    });
  });

  it("tolerates unknown extension fields", () => {
    expect(
      parseProblemDetails({ ...validProblem, futureExtension: "value" }),
    ).not.toBeNull();
  });

  it("keeps a non-default Problem type as opaque metadata", () => {
    expect(
      parseProblemDetails({
        ...validProblem,
        type: "urn:opaque-problem-type",
      }),
    ).toMatchObject({
      code: "VALIDATION_ERROR",
      type: "urn:opaque-problem-type",
    });
  });

  it.each([
    "type",
    "title",
    "status",
    "detail",
    "instance",
    "code",
    "requestId",
  ] as const)("rejects a missing %s field", (field) => {
    const value: Record<string, unknown> = { ...validProblem };
    delete value[field];

    expect(parseProblemDetails(value)).toBeNull();
  });

  it("rejects wrong primitive types", () => {
    expect(parseProblemDetails({ ...validProblem, status: "422" })).toBeNull();
  });

  it("rejects an invalid requestId format", () => {
    expect(
      parseProblemDetails({ ...validProblem, requestId: "not-a-uuid" }),
    ).toBeNull();
  });

  it("rejects an invalid errors shape", () => {
    expect(
      parseProblemDetails({
        ...validProblem,
        errors: [{ field: "q", code: 422 }],
      }),
    ).toBeNull();
  });
});
