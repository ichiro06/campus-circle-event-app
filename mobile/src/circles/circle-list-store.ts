import type { ApiFailure, CirclesApi } from "@/api";

import { toApiFailure } from "./failure-presentation";
import type { CircleListFilters, CircleListItem } from "./types";

export type CircleListErrorPhase = "initial" | "refresh" | "more";

export interface CircleListError {
  failure: ApiFailure;
  occurredAt: Date;
  phase: CircleListErrorPhase;
}

export type CircleListLoadState = "idle" | "initial" | "refresh" | "more";

export interface CircleListSnapshot {
  items: readonly CircleListItem[];
  /** Match count for the filters at the time of the last successful fetch. */
  totalCount: number | null;
  hasMore: boolean;
  loadState: CircleListLoadState;
  /** Time of the last successful fetch whose data is still on screen. */
  lastUpdatedAt: Date | null;
  error: CircleListError | null;
}

const INITIAL_SNAPSHOT: CircleListSnapshot = {
  items: [],
  totalCount: null,
  hasMore: false,
  loadState: "initial",
  lastUpdatedAt: null,
  error: null,
};

/**
 * Appends only Circles whose ID is not shown yet. most_favorited is a live ranking, so a Circle
 * may legitimately appear on two pages (docs/api-contract.md 4.2); the first position wins.
 */
export function mergeUniqueById(
  existing: readonly CircleListItem[],
  incoming: readonly CircleListItem[],
): CircleListItem[] {
  const seen = new Set(existing.map((item) => item.id));
  const merged = [...existing];

  for (const item of incoming) {
    if (!seen.has(item.id)) {
      seen.add(item.id);
      merged.push(item);
    }
  }

  return merged;
}

/**
 * Cursor pagination over GET /api/v1/circles for one fixed set of filters.
 *
 * The cursor is opaque: it is kept exactly as received and sent back unchanged, never decoded.
 * A new filter set means a new store, so results for other filters can never be mixed in.
 */
export class CircleListStore {
  private snapshot: CircleListSnapshot = INITIAL_SNAPSHOT;
  private readonly listeners = new Set<() => void>();
  private cursor: string | null = null;
  private controller: AbortController | null = null;
  private generation = 0;

  constructor(
    private readonly api: CirclesApi,
    private readonly filters: CircleListFilters,
  ) {}

  subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);

    return () => {
      this.listeners.delete(listener);
    };
  };

  getSnapshot = (): CircleListSnapshot => this.snapshot;

  /** Safe to call again after stop(): it refetches only if no first page has arrived yet. */
  start(): void {
    if (this.snapshot.lastUpdatedAt === null && this.snapshot.error === null) {
      void this.fetchFirstPage("initial");
    }
  }

  /** Cancels in-flight work and ignores any late response. */
  stop(): void {
    this.generation += 1;
    this.controller?.abort();
    this.controller = null;
  }

  loadMore = (): void => {
    // After a failure the user decides when to retry, so scrolling cannot loop on an error.
    if (
      this.snapshot.loadState !== "idle" ||
      this.cursor === null ||
      this.snapshot.error !== null
    ) {
      return;
    }

    void this.fetchNextPage();
  };

  /** Drops the cursor and refetches the first page, keeping the shown items meanwhile. */
  refresh = (): void => {
    if (this.snapshot.loadState === "refresh") {
      return;
    }

    void this.fetchFirstPage("refresh");
  };

  /** Repeats whatever failed last: the next page, or the first page. */
  retry = (): void => {
    if (this.snapshot.error?.phase === "more" && this.cursor !== null) {
      void this.fetchNextPage();
      return;
    }

    void this.fetchFirstPage(
      this.snapshot.items.length === 0 ? "initial" : "refresh",
    );
  };

  private update(changes: Partial<CircleListSnapshot>): void {
    this.snapshot = { ...this.snapshot, ...changes };

    for (const listener of this.listeners) {
      listener();
    }
  }

  private begin(phase: Exclude<CircleListLoadState, "idle">): {
    generation: number;
    signal: AbortSignal;
  } {
    this.controller?.abort();
    this.controller = new AbortController();
    this.generation += 1;
    this.update({ loadState: phase, error: null });

    return { generation: this.generation, signal: this.controller.signal };
  }

  private fail(
    caught: unknown,
    phase: CircleListErrorPhase,
  ): ApiFailure | null {
    const failure = toApiFailure(caught);

    if (failure.kind === "cancelled") {
      return null;
    }

    this.update({
      error: { failure, occurredAt: new Date(), phase },
      loadState: "idle",
    });

    return failure;
  }

  private async fetchFirstPage(phase: "initial" | "refresh"): Promise<void> {
    this.cursor = null;
    const { generation, signal } = this.begin(phase);

    try {
      const response = await this.api.listCircles(this.filters, { signal });

      if (generation !== this.generation) {
        return;
      }

      this.cursor = response.page.nextCursor ?? null;
      this.update({
        items: mergeUniqueById([], response.data),
        totalCount: response.page.totalCount,
        hasMore: response.page.hasMore && this.cursor !== null,
        lastUpdatedAt: new Date(),
        loadState: "idle",
      });
    } catch (caught) {
      if (generation === this.generation) {
        this.fail(caught, phase);
      }
    }
  }

  private async fetchNextPage(): Promise<void> {
    const cursor = this.cursor;

    if (cursor === null) {
      return;
    }

    const { generation, signal } = this.begin("more");

    try {
      const response = await this.api.listCircles(
        { ...this.filters, cursor },
        { signal },
      );

      if (generation !== this.generation) {
        return;
      }

      this.cursor = response.page.nextCursor ?? null;
      this.update({
        items: mergeUniqueById(this.snapshot.items, response.data),
        totalCount: response.page.totalCount,
        hasMore: response.page.hasMore && this.cursor !== null,
        lastUpdatedAt: new Date(),
        loadState: "idle",
      });
    } catch (caught) {
      if (generation !== this.generation) {
        return;
      }

      const failure = toApiFailure(caught);

      if (
        failure.kind === "problem" &&
        failure.problem.code === "INVALID_CURSOR"
      ) {
        // The cursor expired or no longer matches: drop it and start again from the first page.
        void this.fetchFirstPage("refresh");
        return;
      }

      this.fail(caught, "more");
    }
  }
}
