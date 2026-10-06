import {
  act,
  fireEvent,
  screen,
  waitFor,
} from "@testing-library/react-native";
import { router } from "expo-router";

import HomeScreen from "../src/app/(tabs)/index";
import { mergeUniqueById } from "../src/circles/use-paginated-circles";
import {
  circleId,
  createMockApi,
  makeCircle,
  makeListResponse,
  networkFailure,
  problemFailure,
  REQUEST_ID,
} from "../test-support/circles";
import { renderWithApi } from "../test-support/render";

jest.mock("expo-router", () => ({
  ...jest.requireActual("expo-router"),
  router: { back: jest.fn(), canGoBack: jest.fn(), push: jest.fn(), replace: jest.fn() },
  useLocalSearchParams: jest.fn(),
}));

const OPAQUE_CURSOR = "opaque+/=cursor.value";

function deferred<Value>() {
  let resolve: (value: Value) => void = () => {};
  let reject: (reason: unknown) => void = () => {};
  const promise = new Promise<Value>((res, rej) => {
    resolve = res;
    reject = rej;
  });

  return { promise, reject, resolve };
}

async function pullToRefresh() {
  const list = screen.getByTestId("circle-list");

  await act(async () => {
    list.props.refreshControl.props.onRefresh();
  });
}

async function scrollToEnd() {
  await act(async () => {
    fireEvent(screen.getByTestId("circle-list"), "endReached");
  });
}

describe("HomeScreen", () => {
  afterEach(() => {
    jest.useRealTimers();
    jest.restoreAllMocks();
  });

  it("requests the public list ordered by most_favorited, without a cursor", async () => {
    const { api, listCircles } = createMockApi();
    listCircles.mockResolvedValue(makeListResponse({ items: [makeCircle(1)] }));

    await renderWithApi(<HomeScreen />, api);
    await screen.findByText("テストサークル1");

    expect(listCircles).toHaveBeenCalledTimes(1);
    expect(listCircles.mock.calls[0]?.[0]).toEqual({ sort: "most_favorited" });
    expect(screen.getByText("サークルを見つけよう")).toBeTruthy();
  });

  it("renders the loaded Circles and never shows favorite counts", async () => {
    const { api, listCircles } = createMockApi();
    listCircles.mockResolvedValue(
      makeListResponse({ items: [makeCircle(1), makeCircle(2)] }),
    );

    await renderWithApi(<HomeScreen />, api);

    expect(await screen.findByText("テストサークル1")).toBeTruthy();
    expect(screen.getByText("テストサークル2")).toBeTruthy();
    expect(screen.queryByText(/お気に入り数|favorite/i)).toBeNull();
    expect(screen.queryByText(/\d+ ?件/)).toBeNull();
  });

  it("shows nothing for the first 300ms and then an accessible skeleton", async () => {
    jest.useFakeTimers();
    const { api, listCircles } = createMockApi();
    const pending = deferred<ReturnType<typeof makeListResponse>>();
    listCircles.mockReturnValue(pending.promise);

    await renderWithApi(<HomeScreen />, api);

    await act(async () => {
      jest.advanceTimersByTime(299);
    });
    expect(screen.queryByRole("progressbar")).toBeNull();

    await act(async () => {
      jest.advanceTimersByTime(1);
    });
    expect(screen.getByRole("progressbar")).toBeTruthy();
    expect(screen.getByLabelText("読み込み中です")).toBeTruthy();

    await act(async () => {
      pending.resolve(makeListResponse({ items: [makeCircle(1)] }));
    });
    expect(screen.queryByRole("progressbar")).toBeNull();
    expect(screen.getByText("テストサークル1")).toBeTruthy();
  });

  it("does not flash a skeleton when the response arrives immediately", async () => {
    jest.useFakeTimers();
    const { api, listCircles } = createMockApi();
    listCircles.mockResolvedValue(makeListResponse({ items: [makeCircle(1)] }));

    await renderWithApi(<HomeScreen />, api);
    await act(async () => {
      jest.advanceTimersByTime(1_000);
    });

    expect(screen.queryByRole("progressbar")).toBeNull();
    expect(screen.getByText("テストサークル1")).toBeTruthy();
  });

  it("explains an empty result and offers a reload", async () => {
    const { api, listCircles } = createMockApi();
    listCircles.mockResolvedValue(makeListResponse({ items: [] }));

    await renderWithApi(<HomeScreen />, api);
    await screen.findByText("表示できるサークルがありません");

    await fireEvent.press(screen.getByRole("button", { name: "再読み込み" }));
    await waitFor(() => expect(listCircles).toHaveBeenCalledTimes(2));
  });

  it("shows an error with the request ID and recovers on retry", async () => {
    const { api, listCircles } = createMockApi();
    listCircles
      .mockRejectedValueOnce(problemFailure(500, "INTERNAL_ERROR"))
      .mockResolvedValueOnce(makeListResponse({ items: [makeCircle(1)] }));

    await renderWithApi(<HomeScreen />, api);

    expect(await screen.findByText("サーバーで問題が発生しました")).toBeTruthy();
    expect(screen.getByText(`問い合わせID: ${REQUEST_ID}`)).toBeTruthy();
    // Server-supplied title/detail never reach the screen.
    expect(screen.queryByText(/SELECT|internal/)).toBeNull();

    await fireEvent.press(screen.getByRole("button", { name: "再試行" }));

    expect(await screen.findByText("テストサークル1")).toBeTruthy();
    expect(screen.queryByText("サーバーで問題が発生しました")).toBeNull();
  });

  it("shows the offline state with a retry when nothing was loaded", async () => {
    const { api, listCircles } = createMockApi();
    listCircles.mockRejectedValue(networkFailure());

    await renderWithApi(<HomeScreen />, api);

    expect(await screen.findByText("オフラインです")).toBeTruthy();
    expect(screen.getByRole("button", { name: "再試行" })).toBeTruthy();
  });

  it("passes nextCursor back unchanged and appends the next page", async () => {
    const { api, listCircles } = createMockApi();
    listCircles
      .mockResolvedValueOnce(
        makeListResponse({ items: [makeCircle(1)], nextCursor: OPAQUE_CURSOR }),
      )
      .mockResolvedValueOnce(makeListResponse({ items: [makeCircle(2)] }));

    await renderWithApi(<HomeScreen />, api);
    await screen.findByText("テストサークル1");
    await scrollToEnd();

    expect(await screen.findByText("テストサークル2")).toBeTruthy();
    expect(screen.getByText("テストサークル1")).toBeTruthy();
    expect(listCircles).toHaveBeenCalledTimes(2);
    expect(listCircles.mock.calls[1]?.[0]).toEqual({
      cursor: OPAQUE_CURSOR,
      sort: "most_favorited",
    });
  });

  it("does not request another page once the last page was reached", async () => {
    const { api, listCircles } = createMockApi();
    listCircles.mockResolvedValue(makeListResponse({ items: [makeCircle(1)] }));

    await renderWithApi(<HomeScreen />, api);
    await screen.findByText("テストサークル1");
    await scrollToEnd();

    expect(listCircles).toHaveBeenCalledTimes(1);
  });

  it("keeps a Circle that reappears on a later page visible exactly once", async () => {
    const consoleError = jest.spyOn(console, "error").mockImplementation(() => {});
    const { api, listCircles } = createMockApi();
    listCircles
      .mockResolvedValueOnce(
        makeListResponse({
          items: [makeCircle(1), makeCircle(2)],
          nextCursor: OPAQUE_CURSOR,
        }),
      )
      .mockResolvedValueOnce(
        makeListResponse({ items: [makeCircle(2), makeCircle(3)] }),
      );

    await renderWithApi(<HomeScreen />, api);
    await screen.findByText("テストサークル2");
    await scrollToEnd();

    expect(await screen.findByText("テストサークル3")).toBeTruthy();
    expect(screen.getAllByText("テストサークル2")).toHaveLength(1);
    expect(consoleError).not.toHaveBeenCalled();
  });

  it("discards the cursor and reloads from the first page on INVALID_CURSOR", async () => {
    const { api, listCircles } = createMockApi();
    listCircles
      .mockResolvedValueOnce(
        makeListResponse({ items: [makeCircle(1)], nextCursor: OPAQUE_CURSOR }),
      )
      .mockRejectedValueOnce(problemFailure(400, "INVALID_CURSOR"))
      .mockResolvedValueOnce(
        makeListResponse({ items: [makeCircle(5)], nextCursor: "fresh-cursor" }),
      );

    await renderWithApi(<HomeScreen />, api);
    await screen.findByText("テストサークル1");
    await scrollToEnd();

    expect(await screen.findByText("テストサークル5")).toBeTruthy();
    expect(screen.queryByText("テストサークル1")).toBeNull();
    expect(listCircles).toHaveBeenCalledTimes(3);
    expect(listCircles.mock.calls[2]?.[0]).toEqual({ sort: "most_favorited" });
    expect(screen.queryByText("続きを読み込めませんでした")).toBeNull();
  });

  it("refreshes from the first page, keeping the sort and dropping the cursor", async () => {
    const { api, listCircles } = createMockApi();
    listCircles
      .mockResolvedValueOnce(
        makeListResponse({ items: [makeCircle(1)], nextCursor: OPAQUE_CURSOR }),
      )
      .mockResolvedValueOnce(makeListResponse({ items: [makeCircle(7)] }));

    await renderWithApi(<HomeScreen />, api);
    await screen.findByText("テストサークル1");
    await pullToRefresh();

    expect(await screen.findByText("テストサークル7")).toBeTruthy();
    expect(screen.queryByText("テストサークル1")).toBeNull();
    expect(listCircles.mock.calls[1]?.[0]).toEqual({ sort: "most_favorited" });
  });

  it("keeps earlier data and shows an offline banner when a refresh fails", async () => {
    const { api, listCircles } = createMockApi();
    listCircles
      .mockResolvedValueOnce(makeListResponse({ items: [makeCircle(1)] }))
      .mockRejectedValueOnce(networkFailure());

    await renderWithApi(<HomeScreen />, api);
    await screen.findByText("テストサークル1");
    await pullToRefresh();

    expect(await screen.findByText("オフラインです")).toBeTruthy();
    expect(screen.getByText("テストサークル1")).toBeTruthy();
    expect(screen.getByText(/最終更新 \d{2}:\d{2}/)).toBeTruthy();
  });

  it("shows the Retry-After time for a 429", async () => {
    const { api, listCircles } = createMockApi();
    listCircles.mockRejectedValue(
      problemFailure(429, "RATE_LIMITED", { retryAfterMs: 30_000 }),
    );

    await renderWithApi(<HomeScreen />, api);

    expect(await screen.findByText("しばらくお待ちください")).toBeTruthy();
    expect(screen.getByText(/約30秒後（\d{2}:\d{2}以降）に再試行できます/)).toBeTruthy();
  });

  it("lets the user retry a failed next page without losing the loaded ones", async () => {
    const { api, listCircles } = createMockApi();
    listCircles
      .mockResolvedValueOnce(
        makeListResponse({ items: [makeCircle(1)], nextCursor: OPAQUE_CURSOR }),
      )
      .mockRejectedValueOnce(problemFailure(503, "SERVICE_UNAVAILABLE"))
      .mockResolvedValueOnce(makeListResponse({ items: [makeCircle(2)] }));

    await renderWithApi(<HomeScreen />, api);
    await screen.findByText("テストサークル1");
    await scrollToEnd();

    expect(await screen.findByText("一時的に利用できません")).toBeTruthy();
    expect(screen.getByText("テストサークル1")).toBeTruthy();

    // Scrolling again must not loop on the failure.
    await scrollToEnd();
    expect(listCircles).toHaveBeenCalledTimes(2);

    await fireEvent.press(screen.getByRole("button", { name: "再試行" }));
    expect(await screen.findByText("テストサークル2")).toBeTruthy();
    expect(listCircles.mock.calls[2]?.[0]).toEqual({
      cursor: OPAQUE_CURSOR,
      sort: "most_favorited",
    });
  });

  it("opens the Circle detail route when a card is pressed", async () => {
    const { api, listCircles } = createMockApi();
    listCircles.mockResolvedValue(makeListResponse({ items: [makeCircle(3)] }));

    await renderWithApi(<HomeScreen />, api);
    await screen.findByText("テストサークル3");
    await fireEvent.press(screen.getByRole("button", { name: /テストサークル3/ }));

    expect(router.push).toHaveBeenCalledWith({
      params: { circleId: circleId(3) },
      pathname: "/circles/[circleId]",
    });
  });
});

describe("mergeUniqueById", () => {
  it("keeps the first position and drops later duplicates", () => {
    const merged = mergeUniqueById(
      [makeCircle(1), makeCircle(2)],
      [makeCircle(2), makeCircle(3), makeCircle(3)],
    );

    expect(merged.map((item) => item.id)).toEqual([
      circleId(1),
      circleId(2),
      circleId(3),
    ]);
  });
});
