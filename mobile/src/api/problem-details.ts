import type { operations } from "./generated/openapi";

type ListProblemDetails =
  operations["listPublicCircles"]["responses"][400 | 422 | 500 | 503]["content"]["application/problem+json"];

type DetailProblemDetails =
  operations["getPublicCircle"]["responses"][404 | 422 | 500 | 503]["content"]["application/problem+json"];

type GeneratedProblemDetails = ListProblemDetails | DetailProblemDetails;

export type ProblemDetails = GeneratedProblemDetails & {
  type: string;
};

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.length > 0;
}

function hasValidErrors(value: unknown): boolean {
  if (value === undefined || value === null) {
    return true;
  }

  return (
    Array.isArray(value) &&
    value.every(
      (item) =>
        isRecord(item) &&
        isNonEmptyString(item.field) &&
        isNonEmptyString(item.code),
    )
  );
}

export function parseProblemDetails(value: unknown): ProblemDetails | null {
  if (!isRecord(value)) {
    return null;
  }

  if (
    !isNonEmptyString(value.type) ||
    !isNonEmptyString(value.title) ||
    !Number.isInteger(value.status) ||
    (value.status as number) < 100 ||
    (value.status as number) > 599 ||
    !isNonEmptyString(value.detail) ||
    !isNonEmptyString(value.instance) ||
    !isNonEmptyString(value.code) ||
    !isNonEmptyString(value.requestId) ||
    !UUID_PATTERN.test(value.requestId) ||
    !hasValidErrors(value.errors)
  ) {
    return null;
  }

  return value as ProblemDetails;
}
