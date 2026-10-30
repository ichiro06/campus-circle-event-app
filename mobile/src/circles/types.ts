import type {
  GetCircleResponse,
  ListCirclesQuery,
  ListCirclesResponse,
  ListTagsResponse,
} from "@/api";

export type CircleListItem = ListCirclesResponse["data"][number];
export type CircleDetail = GetCircleResponse["data"];
/** A selectable tag from the public tag catalog (GET /api/v1/tags). */
export type PublicTag = ListTagsResponse["data"][number];

export type CircleSort = NonNullable<ListCirclesQuery["sort"]>;
export type OfficialStatus = CircleListItem["officialStatus"];
export type CircleType = CircleListItem["circleType"];

/** The list query without the cursor, which only the pagination hook may set. */
export type CircleListFilters = Omit<ListCirclesQuery, "cursor" | "limit">;
