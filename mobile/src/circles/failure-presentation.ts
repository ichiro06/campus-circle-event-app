import { isApiClientError, type ApiFailure } from "@/api";

import { formatClockTime } from "./formatting";

export type FailureKind =
  | "offline"
  | "timeout"
  | "notFound"
  | "invalidRequest"
  | "rateLimited"
  | "unavailable"
  | "serverError"
  | "unexpected";

export interface FailurePresentation {
  kind: FailureKind;
  title: string;
  description: string;
  /** Present only when the server returned a Problem Details body. */
  requestId?: string;
  /** False when retrying with the same request cannot change the outcome (for example 404). */
  canRetry: boolean;
}

/** Normalizes anything a request may throw into an ApiFailure. */
export function toApiFailure(error: unknown): ApiFailure {
  if (isApiClientError(error)) {
    return error.failure;
  }

  return { kind: "unexpectedResponse" };
}

function describeRateLimit(
  retryAfterMs: number | undefined,
  occurredAt: Date,
): string {
  const base = "アクセスが集中しています。しばらく待ってから再試行してください。";

  if (retryAfterMs === undefined) {
    return base;
  }

  const seconds = Math.max(1, Math.ceil(retryAfterMs / 1_000));
  const availableAt = new Date(occurredAt.getTime() + retryAfterMs);

  return `${base}約${seconds}秒後（${formatClockTime(availableAt)}以降）に再試行できます。`;
}

function hasFieldError(failure: ApiFailure, field: string): boolean {
  return (
    failure.kind === "problem" &&
    (failure.problem.errors ?? []).some((item) => item.field === field)
  );
}

/**
 * Maps a failure to user-facing copy. Server-supplied title/detail are deliberately not shown:
 * only the requestId is surfaced, so internal messages cannot leak into the UI.
 */
export function describeFailure(
  failure: ApiFailure,
  occurredAt: Date = new Date(),
): FailurePresentation {
  const requestId =
    failure.kind === "problem" ? failure.problem.requestId : undefined;
  const status =
    failure.kind === "problem" || failure.kind === "unexpectedResponse"
      ? failure.httpStatus
      : undefined;
  const retryAfterMs =
    failure.kind === "problem" || failure.kind === "unexpectedResponse"
      ? failure.retryAfterMs
      : undefined;

  if (failure.kind === "network") {
    return {
      kind: "offline",
      title: "オフラインです",
      description:
        "インターネットに接続できないか、サーバーに接続できません。接続を確認して再試行してください。",
      canRetry: true,
    };
  }

  if (failure.kind === "timeout") {
    return {
      kind: "timeout",
      title: "通信がタイムアウトしました",
      description:
        "接続が遅いか、サーバーが応答していません。時間をおいて再試行してください。",
      canRetry: true,
    };
  }

  if (status === 404) {
    return {
      kind: "notFound",
      title: "表示できません",
      description: "現在このサークル情報を表示できません。",
      requestId,
      canRetry: false,
    };
  }

  if (status === 429) {
    return {
      kind: "rateLimited",
      title: "しばらくお待ちください",
      description: describeRateLimit(retryAfterMs, occurredAt),
      requestId,
      canRetry: true,
    };
  }

  if (status === 422) {
    return {
      kind: "invalidRequest",
      title: "検索条件を確認してください",
      description: hasFieldError(failure, "q")
        ? "キーワードを処理できませんでした。内容を変更して再度お試しください。"
        : "指定した条件を処理できませんでした。条件を変更して再度お試しください。",
      requestId,
      canRetry: false,
    };
  }

  if (
    failure.kind === "problem" &&
    failure.problem.code === "INVALID_CURSOR"
  ) {
    return {
      kind: "invalidRequest",
      title: "続きを読み込めませんでした",
      description:
        "一覧の続きを読み込むための情報が古くなりました。最初から読み込み直してください。",
      requestId,
      canRetry: true,
    };
  }

  if (status === 503) {
    return {
      kind: "unavailable",
      title: "一時的に利用できません",
      description:
        "サーバーが混み合っているか、メンテナンス中です。時間をおいて再試行してください。",
      requestId,
      canRetry: true,
    };
  }

  if (status !== undefined && status >= 500) {
    return {
      kind: "serverError",
      title: "サーバーで問題が発生しました",
      description: "時間をおいて再試行してください。",
      requestId,
      canRetry: true,
    };
  }

  return {
    kind: "unexpected",
    title: "読み込めませんでした",
    description:
      "予期しない応答を受信しました。問題が続く場合は、問い合わせIDをお知らせください。",
    requestId,
    canRetry: true,
  };
}
