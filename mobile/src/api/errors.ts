import type { ProblemDetails } from "./problem-details";

export type ApiFailure =
  | {
      kind: "problem";
      httpStatus: number;
      problem: ProblemDetails;
    }
  | {
      kind: "network";
      cause?: unknown;
    }
  | {
      kind: "timeout";
      timeoutMs: number;
    }
  | {
      kind: "cancelled";
    }
  | {
      kind: "unexpectedResponse";
      httpStatus?: number;
      contentType?: string;
    };

function getFailureMessage(failure: ApiFailure): string {
  switch (failure.kind) {
    case "problem":
      return `API request failed with status ${failure.httpStatus}`;
    case "network":
      return "Network request failed";
    case "timeout":
      return `API request timed out after ${failure.timeoutMs}ms`;
    case "cancelled":
      return "API request was cancelled";
    case "unexpectedResponse":
      return "API returned an unexpected response";
  }
}

export class ApiClientError extends Error {
  constructor(public readonly failure: ApiFailure) {
    super(getFailureMessage(failure));
    this.name = "ApiClientError";
  }
}

export function isApiClientError(value: unknown): value is ApiClientError {
  return value instanceof ApiClientError;
}
