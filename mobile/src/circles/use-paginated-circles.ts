import { useEffect, useMemo, useSyncExternalStore } from "react";

import { useCirclesApi } from "./circles-api-context";
import {
  CircleListStore,
  type CircleListError,
} from "./circle-list-store";
import type { CircleListFilters, CircleListItem } from "./types";

export { mergeUniqueById } from "./circle-list-store";
export type { CircleListError } from "./circle-list-store";

export interface PaginatedCircles {
  items: readonly CircleListItem[];
  /** Match count for the current filters at the time of the last successful fetch. */
  totalCount: number | null;
  hasMore: boolean;
  /** True while the first page of a query is loading and nothing is shown yet. */
  isInitialLoading: boolean;
  isRefreshing: boolean;
  isLoadingMore: boolean;
  /** Time of the last successful fetch whose data is still on screen. */
  lastUpdatedAt: Date | null;
  error: CircleListError | null;
  loadMore: () => void;
  /** Drops the cursor and refetches the first page, keeping the shown items meanwhile. */
  refresh: () => void;
  /** Repeats whatever failed last: the next page, or the first page. */
  retry: () => void;
}

/** Cursor pagination over the public Circle list for one set of filters. */
export function usePaginatedCircles(
  filters: CircleListFilters,
): PaginatedCircles {
  const api = useCirclesApi();
  const filtersKey = JSON.stringify(filters);
  const store = useMemo(
    () => new CircleListStore(api, JSON.parse(filtersKey) as CircleListFilters),
    [api, filtersKey],
  );

  useEffect(() => {
    store.start();

    return () => store.stop();
  }, [store]);

  const snapshot = useSyncExternalStore(store.subscribe, store.getSnapshot);

  return {
    items: snapshot.items,
    totalCount: snapshot.totalCount,
    hasMore: snapshot.hasMore,
    isInitialLoading:
      snapshot.loadState === "initial" && snapshot.items.length === 0,
    isRefreshing: snapshot.loadState === "refresh",
    isLoadingMore: snapshot.loadState === "more",
    lastUpdatedAt: snapshot.lastUpdatedAt,
    error: snapshot.error,
    loadMore: store.loadMore,
    refresh: store.refresh,
    retry: store.retry,
  };
}
