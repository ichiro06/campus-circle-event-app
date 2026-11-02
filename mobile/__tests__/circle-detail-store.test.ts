import { ApiClientError } from "../src/api";
import { CircleDetailStore } from "../src/circles/circle-detail-store";
import { circleId, createMockApi, makeDetail, makeDetailResponse, networkFailure } from "../test-support/circles";

function deferred<Value>() {
  let resolve: (value: Value) => void = () => {};
  let reject: (reason: unknown) => void = () => {};
  const promise = new Promise<Value>((res, rej) => { resolve = res; reject = rej; });
  return { promise, resolve, reject };
}

const settle = async () => { await Promise.resolve(); await Promise.resolve(); };

describe("CircleDetailStore", () => {
  it("coalesces start, refresh and retry during the initial read", async () => {
    const pending = deferred<ReturnType<typeof makeDetailResponse>>();
    const { api, getCircle } = createMockApi();
    getCircle.mockReturnValue(pending.promise);
    const store = new CircleDetailStore(api, circleId(1));
    store.start(); store.start(); store.refresh(); store.retry();
    expect(getCircle).toHaveBeenCalledTimes(1);
    expect(store.getSnapshot().isRefreshing).toBe(false);
    pending.resolve(makeDetailResponse(makeDetail(1)));
    await settle();
    expect(store.getSnapshot().isLoading).toBe(false);
  });

  it("retains the exact last successful data and timestamp on refresh failure", async () => {
    const pending = deferred<ReturnType<typeof makeDetailResponse>>();
    const { api, getCircle } = createMockApi();
    getCircle.mockResolvedValueOnce(makeDetailResponse(makeDetail(1))).mockReturnValueOnce(pending.promise);
    const store = new CircleDetailStore(api, circleId(1));
    store.start(); await settle();
    const last = store.getSnapshot();
    store.refresh(); store.retry(); store.refresh();
    expect(getCircle).toHaveBeenCalledTimes(2);
    expect(store.getSnapshot()).toMatchObject({ circle: last.circle, isLoading: true, isRefreshing: true, lastUpdatedAt: last.lastUpdatedAt });
    pending.reject(networkFailure()); await settle();
    expect(store.getSnapshot().circle).toBe(last.circle);
    expect(store.getSnapshot().lastUpdatedAt).toBe(last.lastUpdatedAt);
    expect(store.getSnapshot()).toMatchObject({ isLoading: false, isRefreshing: false, error: { failure: { kind: "network" } } });
  });

  it("distinguishes retry from explicit refresh and can recover", async () => {
    const pending = deferred<ReturnType<typeof makeDetailResponse>>();
    const { api, getCircle } = createMockApi();
    getCircle.mockRejectedValueOnce(networkFailure()).mockReturnValueOnce(pending.promise)
      .mockResolvedValueOnce(makeDetailResponse(makeDetail(1)));
    const store = new CircleDetailStore(api, circleId(1));
    store.start(); await settle();
    store.retry();
    expect(store.getSnapshot()).toMatchObject({ isLoading: true, isRefreshing: false, error: null });
    pending.reject(networkFailure()); await settle();
    store.refresh();
    expect(store.getSnapshot().isRefreshing).toBe(true);
    await settle();
    expect(store.getSnapshot()).toMatchObject({ circle: makeDetail(1), isLoading: false, isRefreshing: false, error: null });
  });

  it.each(["resolve", "reject"] as const)("ignores a late %s after stop and restarts an interrupted first read", async (outcome) => {
    const pending = deferred<ReturnType<typeof makeDetailResponse>>();
    const { api, getCircle } = createMockApi();
    getCircle.mockReturnValueOnce(pending.promise).mockResolvedValueOnce(makeDetailResponse(makeDetail(1)));
    const store = new CircleDetailStore(api, circleId(1));
    store.start();
    const signal = getCircle.mock.calls[0]?.[1]?.signal;
    store.stop();
    expect(signal?.aborted).toBe(true);
    const stopped = store.getSnapshot();
    if (outcome === "resolve") pending.resolve(makeDetailResponse(makeDetail(9)));
    else pending.reject(networkFailure());
    await settle();
    expect(store.getSnapshot()).toBe(stopped);
    store.refresh(); store.retry();
    expect(getCircle).toHaveBeenCalledTimes(1);
    store.start(); await settle();
    expect(getCircle).toHaveBeenCalledTimes(2);
    expect(store.getSnapshot().circle?.id).toBe(circleId(1));
  });

  it("ignores an old refresh even after a newer request has completed", async () => {
    const pending = deferred<ReturnType<typeof makeDetailResponse>>();
    const { api, getCircle } = createMockApi();
    getCircle.mockResolvedValueOnce(makeDetailResponse(makeDetail(1)))
      .mockReturnValueOnce(pending.promise)
      .mockResolvedValueOnce(makeDetailResponse(makeDetail(1, { headline: "new" })));
    const store = new CircleDetailStore(api, circleId(1));
    store.start(); await settle(); store.refresh(); store.stop(); store.start(); store.refresh(); await settle();
    const latest = store.getSnapshot();
    pending.resolve(makeDetailResponse(makeDetail(1, { headline: "stale" })));
    await settle();
    expect(store.getSnapshot()).toBe(latest);
    expect(latest.circle?.headline).toBe("new");
  });

  it("settles indicators on cancellation and allows a subsequent refresh", async () => {
    const { api, getCircle } = createMockApi();
    getCircle.mockRejectedValueOnce(new ApiClientError({ kind: "cancelled" }))
      .mockResolvedValueOnce(makeDetailResponse(makeDetail(1)));
    const store = new CircleDetailStore(api, circleId(1));
    store.start(); await settle();
    expect(store.getSnapshot()).toMatchObject({ isLoading: false, isRefreshing: false, error: null });
    store.refresh(); await settle();
    expect(store.getSnapshot().circle?.id).toBe(circleId(1));
  });
});
