import type { GetCircleResponse, ListCirclesQuery, ListCirclesResponse } from "@/api";

export type CircleListItem = ListCirclesResponse["data"][number];
export type CircleDetail = GetCircleResponse["data"];

export type CircleSort = NonNullable<ListCirclesQuery["sort"]>;
export type OfficialStatus = CircleListItem["officialStatus"];
export type CircleType = CircleListItem["circleType"];

/** The list query without the cursor, which only the pagination hook may set. */
export type CircleListFilters = Omit<ListCirclesQuery, "cursor" | "limit">;
