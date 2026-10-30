import type { operations } from "./generated/openapi";
import { createApiTransport, type ApiTransport } from "./transport";

export type ListCirclesQuery = NonNullable<
  operations["listPublicCircles"]["parameters"]["query"]
>;

export type ListCirclesResponse =
  operations["listPublicCircles"]["responses"][200]["content"]["application/json"];

export type GetCircleResponse =
  operations["getPublicCircle"]["responses"][200]["content"]["application/json"];

export type ListTagsQuery = NonNullable<
  operations["listPublicTags"]["parameters"]["query"]
>;

export type ListTagsResponse =
  operations["listPublicTags"]["responses"][200]["content"]["application/json"];

export interface CircleRequestOptions {
  signal?: AbortSignal;
}

export interface CirclesApi {
  getCircle(
    circleId: string,
    options?: CircleRequestOptions,
  ): Promise<GetCircleResponse>;
  listCircles(
    query?: ListCirclesQuery,
    options?: CircleRequestOptions,
  ): Promise<ListCirclesResponse>;
  /** Public tag catalog (docs/api-contract.md 4.3): active tags only, in API order. */
  listTags(
    query?: ListTagsQuery,
    options?: CircleRequestOptions,
  ): Promise<ListTagsResponse>;
}

export function createCirclesApi(
  transport: ApiTransport = createApiTransport(),
): CirclesApi {
  return {
    getCircle(circleId, options = {}) {
      return transport.request<GetCircleResponse>({
        method: "GET",
        path: `/api/v1/circles/${encodeURIComponent(circleId)}`,
        signal: options.signal,
      });
    },

    listCircles(query = {}, options = {}) {
      return transport.request<ListCirclesResponse>({
        method: "GET",
        path: "/api/v1/circles",
        query,
        signal: options.signal,
      });
    },

    listTags(query = {}, options = {}) {
      return transport.request<ListTagsResponse>({
        method: "GET",
        path: "/api/v1/tags",
        query,
        signal: options.signal,
      });
    },
  };
}
