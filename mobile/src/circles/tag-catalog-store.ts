import type { CirclesApi } from "@/api";

import type { PublicTag } from "./types";

/** docs/api-contract.md 4.3: `limit` defaults to 20 and is capped at 50. */
export const TAG_PAGE_LIMIT = 50;

/**
 * Technical guard against a runaway request chain, not a product limit on the number of tags.
 *
 * 100 pages of TAG_PAGE_LIMIT tags is 5,000 tags, orders of magnitude above any realistic
 * catalog (the initial vocabulary is 7 tags), so a healthy API never reaches it. It only stops a
 * misbehaving API that keeps answering `hasMore: true` with a new cursor each time. Reaching it
 * is a failure: the catalog is never cut off at this size and shown as if it were complete.
 */
export const MAX_TAG_CATALOG_PAGES = 100;

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
 * The API order is kept and `page.totalCount` is never read.
 *
 * A load ends successfully only when the API answers `hasMore: false`. `hasMore: true` without a
 * usable next cursor (missing, empty, blank, or one already sent, which includes a cycle) and a
 * chain longer than MAX_TAG_CATALOG_PAGES are malformed answers and fail the load. The catalog
 * replaces the previous one only after every page has arrived, so a failure part-way never shows
 * a partial catalog, and a late response of a cancelled or superseded load can never overwrite a
 * newer state.
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

      for (let pageCount = 1; ; pageCount += 1) {
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

        if (!response.page.hasMore) {
          break;
        }

        const nextCursor = response.page.nextCursor;

        // trim() only decides whether the value is blank; the cursor itself is sent untouched.
        if (
          typeof nextCursor !== "string" ||
          nextCursor.trim() === "" ||
          requestedCursors.has(nextCursor)
        ) {
          throw new Error("Tag catalog returned hasMore without a usable next cursor");
        }

        if (pageCount >= MAX_TAG_CATALOG_PAGES) {
          throw new Error("Tag catalog exceeded the page limit");
        }

        requestedCursors.add(nextCursor);
        cursor = nextCursor;
      }

      this.update({ tags, status: "ready", hasLoaded: true });
    } catch {
      // A cancelled load is superseded or stopped, and leaves the state to whoever did that.
      // Every other failure, a malformed pagination answer included, is shown as "error" only:
      // the tag catalog is an optional aid and must not turn into a search error or an empty
      // result. `tags` and `hasLoaded` keep the last complete catalog.
      if (generation === this.generation) {
        this.update({ status: "error" });
      }
    }
  }
}
