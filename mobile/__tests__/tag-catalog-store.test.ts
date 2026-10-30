import type { ListTagsResponse } from "../src/api";
import {
  MAX_TAG_CATALOG_PAGES,
  TAG_PAGE_LIMIT,
  TagCatalogStore,
} from "../src/circles/tag-catalog-store";
import {
  createMockApi,
  makeTag,
  makeTagResponse,
  networkFailure,
  problemFailure,
} from "../test-support/circles";

const OPAQUE_CURSOR = "opaque+/=tags.cursor";

function deferred<Value>() {
  let resolve!: (value: Value) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<Value>((res, rej) => {
    resolve = res;
    reject = rej;
  });

  return { promise, reject, resolve };
}

async function flush() {
  await new Promise<void>((resolve) => setImmediate(() => resolve()));
}

function names(store: TagCatalogStore): string[] {
  return store.getSnapshot().tags.map((tag) => tag.name);
}

describe("TagCatalogStore", () => {
  it("loads one page and keeps the API order", async () => {
    const { api, listTags } = createMockApi();
    listTags.mockResolvedValue(
      makeTagResponse({ items: [makeTag(3), makeTag(1), makeTag(2)] }),
    );
    const store = new TagCatalogStore(api);

    store.start();
    expect(store.getSnapshot()).toMatchObject({ hasLoaded: false, status: "loading" });
    await flush();

    expect(names(store)).toEqual(["テストタグ3", "テストタグ1", "テストタグ2"]);
    expect(store.getSnapshot()).toMatchObject({ hasLoaded: true, status: "ready" });
    expect(listTags).toHaveBeenCalledTimes(1);
    expect(listTags.mock.calls[0]?.[0]).toEqual({ limit: TAG_PAGE_LIMIT });
  });

  it("follows the opaque cursor across pages unchanged and never asks for totalCount", async () => {
    const { api, listTags } = createMockApi();
    listTags
      .mockResolvedValueOnce(
        makeTagResponse({ items: [makeTag(1), makeTag(2)], nextCursor: OPAQUE_CURSOR }),
      )
      .mockResolvedValueOnce(makeTagResponse({ items: [makeTag(3)], nextCursor: "second" }))
      .mockResolvedValueOnce(makeTagResponse({ items: [makeTag(4)] }));
    const store = new TagCatalogStore(api);

    store.start();
    await flush();

    expect(names(store)).toEqual(["テストタグ1", "テストタグ2", "テストタグ3", "テストタグ4"]);
    expect(listTags.mock.calls.map(([query]) => query)).toEqual([
      { limit: TAG_PAGE_LIMIT },
      { cursor: OPAQUE_CURSOR, limit: TAG_PAGE_LIMIT },
      { cursor: "second", limit: TAG_PAGE_LIMIT },
    ]);
    expect(JSON.stringify(listTags.mock.calls)).not.toContain("totalCount");
  });

  it("shows nothing of a catalog until its last page has arrived", async () => {
    const { api, listTags } = createMockApi();
    const secondPage = deferred<ListTagsResponse>();
    listTags
      .mockResolvedValueOnce(makeTagResponse({ items: [makeTag(1)], nextCursor: OPAQUE_CURSOR }))
      .mockReturnValueOnce(secondPage.promise);
    const store = new TagCatalogStore(api);

    store.start();
    await flush();
    expect(store.getSnapshot().tags).toEqual([]);

    secondPage.resolve(makeTagResponse({ items: [makeTag(2)] }));
    await flush();
    expect(names(store)).toEqual(["テストタグ1", "テストタグ2"]);
  });

  it("drops a tag that arrives twice across pages", async () => {
    const { api, listTags } = createMockApi();
    listTags
      .mockResolvedValueOnce(makeTagResponse({ items: [makeTag(1)], nextCursor: OPAQUE_CURSOR }))
      .mockResolvedValueOnce(makeTagResponse({ items: [makeTag(1), makeTag(2)] }));
    const store = new TagCatalogStore(api);

    store.start();
    await flush();

    expect(names(store)).toEqual(["テストタグ1", "テストタグ2"]);
  });

  it("treats a 200 with no tags as a normal, loaded, empty catalog", async () => {
    const { api } = createMockApi();
    const store = new TagCatalogStore(api);

    store.start();
    await flush();

    expect(store.getSnapshot()).toMatchObject({ hasLoaded: true, status: "ready", tags: [] });
  });

  it("finishes normally on hasMore=false and does not follow a leftover cursor", async () => {
    const { api, listTags } = createMockApi();
    listTags.mockResolvedValue({
      ...makeTagResponse({ items: [makeTag(1)] }),
      page: { hasMore: false, limit: TAG_PAGE_LIMIT, nextCursor: OPAQUE_CURSOR },
    });
    const store = new TagCatalogStore(api);

    store.start();
    await flush();

    expect(listTags).toHaveBeenCalledTimes(1);
    expect(store.getSnapshot()).toMatchObject({ hasLoaded: true, status: "ready" });
    expect(names(store)).toEqual(["テストタグ1"]);
  });

  describe("malformed pagination answers", () => {
    function hasMorePage(items: number[], nextCursor: string | null | undefined) {
      return {
        ...makeTagResponse({ items: items.map((index) => makeTag(index)) }),
        page: { hasMore: true, limit: TAG_PAGE_LIMIT, nextCursor },
      } as ListTagsResponse;
    }

    it.each([
      ["null", null],
      ["undefined", undefined],
      ["an empty string", ""],
      ["a blank string", "   "],
      ["only whitespace characters", "\t\n\u3000"],
    ])("fails the first load when hasMore=true comes with %s as the cursor", async (_name, cursor) => {
      const { api, listTags } = createMockApi();
      listTags.mockResolvedValue(hasMorePage([1], cursor));
      const store = new TagCatalogStore(api);

      store.start();
      await flush();

      expect(listTags).toHaveBeenCalledTimes(1);
      expect(store.getSnapshot()).toMatchObject({ hasLoaded: false, status: "error", tags: [] });
    });

    it("fails when a later page reports hasMore without a usable cursor, without a partial catalog", async () => {
      const { api, listTags } = createMockApi();
      listTags
        .mockResolvedValueOnce(hasMorePage([1], OPAQUE_CURSOR))
        .mockResolvedValueOnce(hasMorePage([2], ""));
      const store = new TagCatalogStore(api);

      store.start();
      await flush();

      expect(listTags).toHaveBeenCalledTimes(2);
      expect(store.getSnapshot()).toMatchObject({ hasLoaded: false, status: "error", tags: [] });
    });

    it("fails when the same cursor is handed out again", async () => {
      const { api, listTags } = createMockApi();
      listTags
        .mockResolvedValueOnce(hasMorePage([1], "same"))
        .mockResolvedValue(hasMorePage([2], "same"));
      const store = new TagCatalogStore(api);

      store.start();
      await flush();

      expect(listTags).toHaveBeenCalledTimes(2);
      expect(store.getSnapshot()).toMatchObject({ hasLoaded: false, status: "error", tags: [] });
    });

    it("fails on a cycle of cursors (A -> B -> A)", async () => {
      const { api, listTags } = createMockApi();
      listTags
        .mockResolvedValueOnce(hasMorePage([1], "A"))
        .mockResolvedValueOnce(hasMorePage([2], "B"))
        .mockResolvedValue(hasMorePage([3], "A"));
      const store = new TagCatalogStore(api);

      store.start();
      await flush();

      expect(listTags.mock.calls.map(([query]) => query.cursor)).toEqual([undefined, "A", "B"]);
      expect(store.getSnapshot()).toMatchObject({ hasLoaded: false, status: "error", tags: [] });
    });

    it("keeps the last complete catalog when a refresh meets a malformed answer", async () => {
      const { api, listTags } = createMockApi();
      listTags
        .mockResolvedValueOnce(makeTagResponse({ items: [makeTag(1), makeTag(2)] }))
        .mockResolvedValueOnce(hasMorePage([3], OPAQUE_CURSOR))
        .mockResolvedValueOnce(hasMorePage([4], null));
      const store = new TagCatalogStore(api);

      store.start();
      await flush();
      store.refresh();
      await flush();

      expect(store.getSnapshot()).toMatchObject({ hasLoaded: true, status: "error" });
      expect(names(store)).toEqual(["テストタグ1", "テストタグ2"]);
    });

    it("recovers with a later refresh once the answers are well formed", async () => {
      const { api, listTags } = createMockApi();
      listTags
        .mockResolvedValueOnce(hasMorePage([1], null))
        .mockResolvedValueOnce(makeTagResponse({ items: [makeTag(1)] }));
      const store = new TagCatalogStore(api);

      store.start();
      await flush();
      expect(store.getSnapshot().status).toBe("error");
      store.refresh();
      await flush();

      expect(store.getSnapshot()).toMatchObject({ hasLoaded: true, status: "ready" });
      expect(names(store)).toEqual(["テストタグ1"]);
    });

    it("sends a cursor that contains whitespace exactly as received", async () => {
      const { api, listTags } = createMockApi();
      const cursor = "  padded cursor+/=  ";
      listTags
        .mockResolvedValueOnce(hasMorePage([1], cursor))
        .mockResolvedValueOnce(makeTagResponse({ items: [makeTag(2)] }));
      const store = new TagCatalogStore(api);

      store.start();
      await flush();

      expect(listTags.mock.calls[1]?.[0]).toEqual({ cursor, limit: TAG_PAGE_LIMIT });
      expect(names(store)).toEqual(["テストタグ1", "テストタグ2"]);
    });
  });

  describe("page limit", () => {
    it("stops a never-ending chain of fresh cursors after MAX_TAG_CATALOG_PAGES and fails", async () => {
      const { api, listTags } = createMockApi();
      let page = 0;
      listTags.mockImplementation(async () => {
        page += 1;

        return {
          ...makeTagResponse({ items: [makeTag(page)] }),
          page: { hasMore: true, limit: TAG_PAGE_LIMIT, nextCursor: `cursor-${page}` },
        };
      });
      const store = new TagCatalogStore(api);

      store.start();
      await flush();

      expect(listTags).toHaveBeenCalledTimes(MAX_TAG_CATALOG_PAGES);
      expect(store.getSnapshot()).toMatchObject({ hasLoaded: false, status: "error", tags: [] });
    });

    it("still succeeds when the last allowed page reports hasMore=false", async () => {
      const { api, listTags } = createMockApi();
      let page = 0;
      listTags.mockImplementation(async () => {
        page += 1;

        return makeTagResponse({
          items: [makeTag(page)],
          nextCursor: page < MAX_TAG_CATALOG_PAGES ? `cursor-${page}` : undefined,
        });
      });
      const store = new TagCatalogStore(api);

      store.start();
      await flush();

      expect(listTags).toHaveBeenCalledTimes(MAX_TAG_CATALOG_PAGES);
      expect(store.getSnapshot()).toMatchObject({ hasLoaded: true, status: "ready" });
      expect(store.getSnapshot().tags).toHaveLength(MAX_TAG_CATALOG_PAGES);
    });

    it("keeps the last complete catalog when a refresh hits the limit", async () => {
      const { api, listTags } = createMockApi();
      listTags.mockResolvedValueOnce(makeTagResponse({ items: [makeTag(1)] }));
      const store = new TagCatalogStore(api);

      store.start();
      await flush();
      let page = 0;
      listTags.mockImplementation(async () => {
        page += 1;

        return {
          ...makeTagResponse({ items: [makeTag(100 + page)] }),
          page: { hasMore: true, limit: TAG_PAGE_LIMIT, nextCursor: `cursor-${page}` },
        };
      });
      store.refresh();
      await flush();

      expect(store.getSnapshot()).toMatchObject({ hasLoaded: true, status: "error" });
      expect(names(store)).toEqual(["テストタグ1"]);
    });
  });

  it.each([
    ["offline", networkFailure()],
    ["a 503", problemFailure(503, "SERVICE_UNAVAILABLE")],
    ["an invalid cursor", problemFailure(400, "INVALID_CURSOR")],
    ["a non-API error", new Error("boom")],
  ])("ends in an error without tags after %s", async (_name, failure) => {
    const { api, listTags } = createMockApi();
    listTags.mockRejectedValue(failure);
    const store = new TagCatalogStore(api);

    store.start();
    await flush();

    expect(store.getSnapshot()).toMatchObject({ hasLoaded: false, status: "error", tags: [] });
  });

  it("shows no partial catalog when a later page fails", async () => {
    const { api, listTags } = createMockApi();
    listTags
      .mockResolvedValueOnce(makeTagResponse({ items: [makeTag(1)], nextCursor: OPAQUE_CURSOR }))
      .mockRejectedValueOnce(networkFailure());
    const store = new TagCatalogStore(api);

    store.start();
    await flush();

    expect(store.getSnapshot()).toMatchObject({ status: "error", tags: [] });
  });

  it("recovers on refresh after an error", async () => {
    const { api, listTags } = createMockApi();
    listTags
      .mockRejectedValueOnce(networkFailure())
      .mockResolvedValueOnce(makeTagResponse({ items: [makeTag(1)] }));
    const store = new TagCatalogStore(api);

    store.start();
    await flush();
    store.refresh();
    expect(store.getSnapshot().status).toBe("loading");
    await flush();

    expect(store.getSnapshot()).toMatchObject({ hasLoaded: true, status: "ready" });
    expect(names(store)).toEqual(["テストタグ1"]);
  });

  it("keeps the tags shown while a refresh runs and after a refresh fails", async () => {
    const { api, listTags } = createMockApi();
    const refreshed = deferred<ListTagsResponse>();
    listTags
      .mockResolvedValueOnce(makeTagResponse({ items: [makeTag(1)] }))
      .mockReturnValueOnce(refreshed.promise);
    const store = new TagCatalogStore(api);

    store.start();
    await flush();
    store.refresh();

    expect(store.getSnapshot()).toMatchObject({ status: "loading" });
    expect(names(store)).toEqual(["テストタグ1"]);

    refreshed.reject(networkFailure());
    await flush();

    expect(store.getSnapshot()).toMatchObject({ hasLoaded: true, status: "error" });
    expect(names(store)).toEqual(["テストタグ1"]);
  });

  it("replaces the catalog on refresh, so a deactivated tag disappears", async () => {
    const { api, listTags } = createMockApi();
    listTags
      .mockResolvedValueOnce(makeTagResponse({ items: [makeTag(1), makeTag(2)] }))
      .mockResolvedValueOnce(makeTagResponse({ items: [makeTag(2)] }));
    const store = new TagCatalogStore(api);

    store.start();
    await flush();
    store.refresh();
    await flush();

    expect(names(store)).toEqual(["テストタグ2"]);
  });

  it("ignores the late response of a load that a newer refresh superseded", async () => {
    const { api, listTags } = createMockApi();
    const first = deferred<ListTagsResponse>();
    const second = deferred<ListTagsResponse>();
    listTags.mockReturnValueOnce(first.promise).mockReturnValueOnce(second.promise);
    const store = new TagCatalogStore(api);

    store.start();
    store.refresh();
    const firstSignal = listTags.mock.calls[0]?.[1]?.signal as AbortSignal;
    expect(firstSignal.aborted).toBe(true);

    second.resolve(makeTagResponse({ items: [makeTag(2)] }));
    await flush();
    first.resolve(makeTagResponse({ items: [makeTag(1)] }));
    await flush();

    expect(names(store)).toEqual(["テストタグ2"]);
    expect(store.getSnapshot().status).toBe("ready");
  });

  it("does not let a late failure of a superseded load replace the newer state", async () => {
    const { api, listTags } = createMockApi();
    const first = deferred<ListTagsResponse>();
    const second = deferred<ListTagsResponse>();
    listTags.mockReturnValueOnce(first.promise).mockReturnValueOnce(second.promise);
    const store = new TagCatalogStore(api);

    store.start();
    store.refresh();
    second.resolve(makeTagResponse({ items: [makeTag(2)] }));
    await flush();
    first.reject(networkFailure());
    await flush();

    expect(store.getSnapshot()).toMatchObject({ status: "ready" });
    expect(names(store)).toEqual(["テストタグ2"]);
  });

  it("cancels the request on stop() and ignores a response that arrives afterwards", async () => {
    const { api, listTags } = createMockApi();
    const pending = deferred<ListTagsResponse>();
    listTags.mockReturnValueOnce(pending.promise);
    const store = new TagCatalogStore(api);
    const listener = jest.fn();
    store.subscribe(listener);

    store.start();
    const signal = listTags.mock.calls[0]?.[1]?.signal as AbortSignal;
    listener.mockClear();
    store.stop();

    expect(signal.aborted).toBe(true);

    pending.resolve(makeTagResponse({ items: [makeTag(1)] }));
    await flush();

    expect(store.getSnapshot().tags).toEqual([]);
    expect(listener).not.toHaveBeenCalled();
  });

  it("loads again when started after a stop that interrupted the first load", async () => {
    const { api, listTags } = createMockApi();
    listTags
      .mockReturnValueOnce(deferred<ListTagsResponse>().promise)
      .mockResolvedValueOnce(makeTagResponse({ items: [makeTag(1)] }));
    const store = new TagCatalogStore(api);

    store.start();
    store.stop();
    store.start();
    await flush();

    expect(listTags).toHaveBeenCalledTimes(2);
    expect(names(store)).toEqual(["テストタグ1"]);
  });

  it("does not load again when restarted after a completed load", async () => {
    const { api, listTags } = createMockApi();
    listTags.mockResolvedValue(makeTagResponse({ items: [makeTag(1)] }));
    const store = new TagCatalogStore(api);

    store.start();
    await flush();
    store.stop();
    store.start();
    await flush();

    expect(listTags).toHaveBeenCalledTimes(1);
  });

  it("returns to ready, not loading forever, when stop() interrupts a refresh", async () => {
    const { api, listTags } = createMockApi();
    listTags
      .mockResolvedValueOnce(makeTagResponse({ items: [makeTag(1)] }))
      .mockReturnValueOnce(deferred<ListTagsResponse>().promise);
    const store = new TagCatalogStore(api);

    store.start();
    await flush();
    store.refresh();
    store.stop();

    expect(store.getSnapshot()).toMatchObject({ hasLoaded: true, status: "ready" });
    expect(names(store)).toEqual(["テストタグ1"]);
  });
});
