import type { CircleListFilters } from "./types";
import {
  usePaginatedCircles,
  type PaginatedCircles,
} from "./use-paginated-circles";

/**
 * Logged-out Home: the public list ordered by favorite count (docs/coding-readiness.md 3.1).
 * The viewer has no views or interests, so no recommendation logic applies. Personalized Home
 * (Gate B) must replace this single hook, not the Home screen.
 */
export const HOME_CIRCLE_FILTERS: CircleListFilters = {
  sort: "most_favorited",
};

export function useHomeCircles(): PaginatedCircles {
  return usePaginatedCircles(HOME_CIRCLE_FILTERS);
}
