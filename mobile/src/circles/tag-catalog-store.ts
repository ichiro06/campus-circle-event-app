import type { CirclesApi } from "@/api";

import type { PublicTag } from "./types";

/** docs/api-contract.md 4.3: `limit` defaults to 20 and is capped at 50. */
export const TAG_PAGE_LIMIT = 50;

export type TagCatalogStatus = "loading" | "ready" | "error";

export interface TagCatalogSnapshot {
  /** Active tags in the order the API returned them. Empty until a full load has succeeded. */
  tags: readonly PublicTag[];
  /**
   * "loading" covers the first load and a refresh. "error" means the last load failed; `tags`
   * still holds the catalog of the last successful load, if there was one.
   */
  status: TagCatalogStatus;
  /** True once at least one full load has succeeded. */
  hasLoaded: boolean;
}

const INITIAL_SNAPSHOT: TagCatalogSnapshot = {
  tags: [],
  status: "loading",
  hasLoaded: false,
};

/**
 * Loads the whole public tag catalog (GET /api/v1/tags) by following the cursor until the API
 * reports no further page.
 *
 * The cursor is opaque: it is kept exactly as received and sent back unchanged, never decoded.
 * The API order is kept and `page.totalCount` is never read. The catalog replaces the previous
 * one only after every page has arrived, so a failure part-way never shows a partial catalog,
 * and a late response of a cancelled or superseded load can never overwrite a newer state.
 */
export class TagCatalogStore {
  private snapshot: TagCatalogSnapshot = INITIAL_SNAPSHOT;
  private readonly listeners = new Set<() => void>();
  private controller: AbortController | null = null;
  private generation = 0;

  constructor(private readonly api: CirclesApi) {}

  subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);

    return () => {
      this.listeners.delete(listener);
    };
  };

  getSnapshot = (): TagCatalogSnapshot => this.snapshot;

  /** Safe to call again after stop(): it reloads only if nothing has been settled yet. */
  start(): void {
    if (!this.snapshot.hasLoaded && this.snapshot.status === "loading") {
      void this.load();
    }
  }

  /** Cancels in-flight work and ignores any late response. */
  stop(): void {
    this.generation += 1;
    this.controller?.abort();
    this.controller = null;

    // An interrupted refresh would otherwise stay "loading" for good: start() only reloads a
    // catalog that has never been loaded. The tags of the earlier load are still valid.
    if (this.snapshot.status === "loading" && this.snapshot.hasLoaded) {
      this.snapshot = { ...this.snapshot, status: "ready" };
    }
  }

  /** Loads the catalog again. The tags already shown stay until the new catalog has arrived. */
  refresh = (): void => {
    void this.load();
  };

  private update(changes: Partial<TagCatalogSnapshot>): void {
    this.snapshot = { ...this.snapshot, ...changes };

    for (const listener of this.listeners) {
      listener();
    }
  }

  private async load(): Promise<void> {
    this.controller?.abort();
    const controller = new AbortController();
    this.controller = controller;
    this.generation += 1;
    const generation = this.generation;
    this.update({ status: "loading" });

    try {
      const tags: PublicTag[] = [];
      const seenIds = new Set<string>();
      const requestedCursors = new Set<string>();
      let cursor: string | undefined;

      for (;;) {
        const response = await this.api.listTags(
          cursor === undefined
            ? { limit: TAG_PAGE_LIMIT }
            : { cursor, limit: TAG_PAGE_LIMIT },
          { signal: controller.signal },
        );

        if (generation !== this.generation) {
          return;
        }

        for (const tag of response.data) {
          if (!seenIds.has(tag.id)) {
            seenIds.add(tag.id);
            tags.push(tag);
          }
        }

        const nextCursor = response.page.nextCursor ?? null;

        // Stop on a missing cursor, or on one that was already sent, so a misbehaving server
        // can never keep this loop running.
        if (
          !response.page.hasMore ||
          nextCursor === null ||
          requestedCursors.has(nextCursor)
        ) {
          break;
        }

        requestedCursors.add(nextCursor);
        cursor = nextCursor;
      }

      this.update({ tags, status: "ready", hasLoaded: true });
    } catch {
      // A cancelled load is superseded or stopped, and leaves the state to whoever did that.
      // Every other failure is shown as "error" only: the tag catalog is an optional aid and
      // must not turn into a search error or an empty result.
      if (generation === this.generation) {
        this.update({ status: "error" });
      }
    }
  }
}
