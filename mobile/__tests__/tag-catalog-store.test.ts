import type { ListTagsResponse } from "../src/api";
import { TAG_PAGE_LIMIT, TagCatalogStore } from "../src/circles/tag-catalog-store";
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

  it("stops following a cursor that was already sent, or a missing one", async () => {
    const { api, listTags } = createMockApi();
    listTags
      .mockResolvedValueOnce(makeTagResponse({ items: [makeTag(1)], nextCursor: "same" }))
      .mockResolvedValue(makeTagResponse({ items: [makeTag(2)], nextCursor: "same" }));
    const store = new TagCatalogStore(api);

    store.start();
    await flush();

    expect(listTags).toHaveBeenCalledTimes(2);
    expect(names(store)).toEqual(["テストタグ1", "テストタグ2"]);

    const missing = createMockApi();
    missing.listTags.mockResolvedValue({
      ...makeTagResponse({ items: [makeTag(1)] }),
      page: { hasMore: true, limit: 50 },
    });
    const missingStore = new TagCatalogStore(missing.api);
    missingStore.start();
    await flush();

    expect(missing.listTags).toHaveBeenCalledTimes(1);
    expect(names(missingStore)).toEqual(["テストタグ1"]);
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
