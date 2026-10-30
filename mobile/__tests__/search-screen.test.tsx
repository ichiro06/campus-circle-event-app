import { act, fireEvent, screen, waitFor } from "@testing-library/react-native";

import SearchScreen, { SEARCH_DEBOUNCE_MS } from "../src/app/(tabs)/search";
import type { ListTagsResponse } from "../src/api";
import {
  createMockApi,
  makeCircle,
  makeListResponse,
  makeTag,
  makeTagResponse,
  networkFailure,
  problemFailure,
  tagId,
} from "../test-support/circles";
import { renderWithApi } from "../test-support/render";

jest.mock("expo-router", () => ({
  ...jest.requireActual("expo-router"),
  router: { back: jest.fn(), canGoBack: jest.fn(), push: jest.fn(), replace: jest.fn() },
  useLocalSearchParams: jest.fn(),
}));

const OPAQUE_CURSOR = "opaque+/=search.cursor";

async function typeKeyword(text: string) {
  await fireEvent.changeText(screen.getByLabelText("キーワード検索"), text);
}

async function settleDebounce() {
  await act(async () => {
    jest.advanceTimersByTime(SEARCH_DEBOUNCE_MS);
  });
}

function deferred<Value>() {
  let resolve!: (value: Value) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<Value>((res, rej) => {
    resolve = res;
    reject = rej;
  });

  return { promise, reject, resolve };
}

async function pullToRefresh() {
  await act(async () => {
    screen.getByTestId("circle-list").props.refreshControl.props.onRefresh();
  });
}

function lastQuery(listCircles: jest.Mock): unknown {
  return listCircles.mock.calls[listCircles.mock.calls.length - 1]?.[0];
}

describe("SearchScreen", () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("starts with the unfiltered newest list", async () => {
    const { api, listCircles } = createMockApi();
    listCircles.mockResolvedValue(makeListResponse({ items: [makeCircle(1)] }));

    await renderWithApi(<SearchScreen />, api);

    expect(await screen.findByText("テストサークル1")).toBeTruthy();
    expect(listCircles).toHaveBeenCalledTimes(1);
    expect(listCircles.mock.calls[0]?.[0]).toEqual({ sort: "newest" });
  });

  it("sends the trimmed keyword as q after the debounce", async () => {
    const { api, listCircles } = createMockApi();
    listCircles.mockResolvedValue(makeListResponse({ items: [makeCircle(1)] }));

    await renderWithApi(<SearchScreen />, api);
    await typeKeyword("  軽音  ");

    expect(listCircles).toHaveBeenCalledTimes(1);
    await settleDebounce();

    await waitFor(() => expect(listCircles).toHaveBeenCalledTimes(2));
    expect(lastQuery(listCircles)).toEqual({ q: "軽音", sort: "newest" });
  });

  it("searches immediately when the keyboard search key is pressed", async () => {
    const { api, listCircles } = createMockApi();
    listCircles.mockResolvedValue(makeListResponse({ items: [makeCircle(1)] }));

    await renderWithApi(<SearchScreen />, api);
    await typeKeyword("テニス");
    await fireEvent(screen.getByLabelText("キーワード検索"), "submitEditing");

    await waitFor(() => expect(listCircles).toHaveBeenCalledTimes(2));
    expect(lastQuery(listCircles)).toEqual({ q: "テニス", sort: "newest" });
  });

  it("neither sends q nor requests again for a whitespace-only keyword", async () => {
    const { api, listCircles } = createMockApi();
    listCircles.mockResolvedValue(makeListResponse({ items: [makeCircle(1)] }));

    await renderWithApi(<SearchScreen />, api);
    await screen.findByText("テストサークル1");
    await typeKeyword("   　 ");
    await settleDebounce();
    await fireEvent(screen.getByLabelText("キーワード検索"), "submitEditing");

    expect(listCircles).toHaveBeenCalledTimes(1);
    for (const [query] of listCircles.mock.calls) {
      expect(query).not.toHaveProperty("q");
    }
  });

  it("switches the sort between newest and most_favorited", async () => {
    const { api, listCircles } = createMockApi();
    listCircles.mockResolvedValue(makeListResponse({ items: [makeCircle(1)] }));

    await renderWithApi(<SearchScreen />, api);
    await screen.findByText("テストサークル1");
    await fireEvent.press(screen.getByRole("radio", { name: "お気に入り数順" }));

    await waitFor(() => expect(lastQuery(listCircles)).toEqual({ sort: "most_favorited" }));
    expect(screen.getByRole("radio", { name: "お気に入り数順", selected: true })).toBeTruthy();

    await fireEvent.press(screen.getByRole("radio", { name: "新着順" }));
    await waitFor(() => expect(lastQuery(listCircles)).toEqual({ sort: "newest" }));
  });

  it("filters by officialStatus and circleType, keeping the choices in a stable order", async () => {
    const { api, listCircles } = createMockApi();
    listCircles.mockResolvedValue(makeListResponse({ items: [makeCircle(1)] }));

    await renderWithApi(<SearchScreen />, api);
    await screen.findByText("テストサークル1");

    await fireEvent.press(screen.getByRole("checkbox", { name: "公認" }));
    await fireEvent.press(screen.getByRole("checkbox", { name: "部活" }));
    await fireEvent.press(screen.getByRole("checkbox", { name: "サークル" }));

    await waitFor(() =>
      expect(lastQuery(listCircles)).toEqual({
        circleType: ["circle", "club"],
        officialStatus: ["official"],
        sort: "newest",
      }),
    );
    expect(screen.getByRole("checkbox", { name: "公認", checked: true })).toBeTruthy();

    await fireEvent.press(screen.getByRole("checkbox", { name: "公認" }));
    await waitFor(() =>
      expect(lastQuery(listCircles)).toEqual({
        circleType: ["circle", "club"],
        sort: "newest",
      }),
    );
  });

  it("shows the current match count", async () => {
    const { api, listCircles } = createMockApi();
    listCircles.mockResolvedValue(
      makeListResponse({ items: [makeCircle(1)], totalCount: 12 }),
    );

    await renderWithApi(<SearchScreen />, api);

    expect(await screen.findByText("該当 12 件")).toBeTruthy();
  });

  it("explains an empty result and clears every condition from the action", async () => {
    const { api, listCircles } = createMockApi();
    listCircles
      .mockResolvedValueOnce(makeListResponse({ items: [makeCircle(1)] }))
      .mockResolvedValueOnce(makeListResponse({ items: [], totalCount: 0 }))
      .mockResolvedValueOnce(makeListResponse({ items: [makeCircle(1)] }));

    await renderWithApi(<SearchScreen />, api);
    await screen.findByText("テストサークル1");
    await typeKeyword("存在しない");
    await settleDebounce();

    expect(await screen.findByText("条件に合うサークルが見つかりません")).toBeTruthy();
    expect(screen.getByText("該当 0 件")).toBeTruthy();

    await fireEvent.press(screen.getByRole("button", { name: "検索条件を解除" }));

    expect(await screen.findByText("テストサークル1")).toBeTruthy();
    expect(lastQuery(listCircles)).toEqual({ sort: "newest" });
    expect(screen.getByLabelText("キーワード検索").props.value).toBe("");
  });

  it("sends the cursor unchanged together with the active filters", async () => {
    const { api, listCircles } = createMockApi();
    listCircles
      .mockResolvedValueOnce(makeListResponse({ items: [makeCircle(9)], totalCount: 9 }))
      .mockResolvedValueOnce(
        makeListResponse({ items: [makeCircle(1)], nextCursor: OPAQUE_CURSOR, totalCount: 2 }),
      )
      .mockResolvedValueOnce(makeListResponse({ items: [makeCircle(2)], totalCount: 2 }));

    await renderWithApi(<SearchScreen />, api);
    await screen.findByText("テストサークル9");
    await fireEvent.press(screen.getByRole("checkbox", { name: "公認" }));
    await screen.findByText("テストサークル1");
    await act(async () => {
      fireEvent(screen.getByTestId("circle-list"), "endReached");
    });

    expect(await screen.findByText("テストサークル2")).toBeTruthy();
    expect(listCircles.mock.calls[2]?.[0]).toEqual({
      cursor: OPAQUE_CURSOR,
      officialStatus: ["official"],
      sort: "newest",
    });
    expect(screen.getByText("該当 2 件")).toBeTruthy();
  });

  it("shows validation guidance for a 422", async () => {
    const { api, listCircles } = createMockApi();
    listCircles.mockRejectedValue(problemFailure(422, "VALIDATION_ERROR"));

    await renderWithApi(<SearchScreen />, api);

    expect(await screen.findByText("検索条件を確認してください")).toBeTruthy();
    // 422 cannot be fixed by repeating the same request.
    expect(screen.queryByRole("button", { name: "再試行" })).toBeNull();
  });

  it("clears the keyword with the clear button", async () => {
    const { api, listCircles } = createMockApi();
    listCircles.mockResolvedValue(makeListResponse({ items: [makeCircle(1)] }));

    await renderWithApi(<SearchScreen />, api);
    await screen.findByText("テストサークル1");
    await typeKeyword("軽音");
    await settleDebounce();
    await waitFor(() => expect(lastQuery(listCircles)).toEqual({ q: "軽音", sort: "newest" }));

    await fireEvent.press(screen.getByRole("button", { name: "入力を消去" }));

    await waitFor(() => expect(lastQuery(listCircles)).toEqual({ sort: "newest" }));
    expect(screen.getByLabelText("キーワード検索").props.value).toBe("");
  });
});

describe("SearchScreen tag filter", () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  function setup(tags = [makeTag(1), makeTag(2), makeTag(3)]) {
    const mocks = createMockApi();
    mocks.listCircles.mockResolvedValue(makeListResponse({ items: [makeCircle(1)] }));
    mocks.listTags.mockResolvedValue(makeTagResponse({ items: tags }));

    return mocks;
  }

  it("shows the tags from the API, in API order, as unselected multi-select choices", async () => {
    const { api, listTags } = setup([makeTag(3), makeTag(1), makeTag(2)]);

    await renderWithApi(<SearchScreen />, api);

    expect(await screen.findByRole("checkbox", { name: "テストタグ3" })).toBeTruthy();
    const labels = screen
      .getAllByRole("checkbox")
      .map((chip) => chip.props.accessibilityLabel)
      .filter((label: string) => label.startsWith("テストタグ"));
    expect(labels).toEqual(["テストタグ3", "テストタグ1", "テストタグ2"]);
    expect(screen.getByRole("checkbox", { name: "テストタグ1", checked: false })).toBeTruthy();
    expect(screen.getByText("タグ")).toBeTruthy();
    expect(listTags).toHaveBeenCalledTimes(1);
  });

  it("loads every page of the catalog", async () => {
    const { api, listTags } = setup();
    listTags
      .mockReset()
      .mockResolvedValueOnce(
        makeTagResponse({ items: [makeTag(1), makeTag(2)], nextCursor: OPAQUE_CURSOR }),
      )
      .mockResolvedValueOnce(makeTagResponse({ items: [makeTag(3)] }));

    await renderWithApi(<SearchScreen />, api);

    expect(await screen.findByRole("checkbox", { name: "テストタグ3" })).toBeTruthy();
    expect(screen.getByRole("checkbox", { name: "テストタグ1" })).toBeTruthy();
    expect(listTags.mock.calls[1]?.[0]).toMatchObject({ cursor: OPAQUE_CURSOR });
  });

  it("selects and clears several tags and reflects it in the accessibility state", async () => {
    const { api } = setup();

    await renderWithApi(<SearchScreen />, api);
    await fireEvent.press(await screen.findByRole("checkbox", { name: "テストタグ1" }));
    await fireEvent.press(screen.getByRole("checkbox", { name: "テストタグ3" }));

    expect(screen.getByRole("checkbox", { name: "テストタグ1", checked: true })).toBeTruthy();
    expect(screen.getByRole("checkbox", { name: "テストタグ3", checked: true })).toBeTruthy();
    expect(screen.getByRole("checkbox", { name: "テストタグ2", checked: false })).toBeTruthy();

    await fireEvent.press(screen.getByRole("checkbox", { name: "テストタグ1" }));

    expect(screen.getByRole("checkbox", { name: "テストタグ1", checked: false })).toBeTruthy();
    expect(screen.getByRole("checkbox", { name: "テストタグ3", checked: true })).toBeTruthy();
  });

  it("sends the UUIDs from the API as tagId, in catalog order, and drops it when cleared", async () => {
    const { api, listCircles } = setup([makeTag(3), makeTag(1), makeTag(2)]);

    await renderWithApi(<SearchScreen />, api);
    await fireEvent.press(await screen.findByRole("checkbox", { name: "テストタグ2" }));
    await waitFor(() =>
      expect(lastQuery(listCircles)).toEqual({ sort: "newest", tagId: [tagId(2)] }),
    );
    await fireEvent.press(screen.getByRole("checkbox", { name: "テストタグ3" }));

    // Pressed second, but listed by the catalog order: equal selections give equal queries.
    await waitFor(() =>
      expect(lastQuery(listCircles)).toEqual({
        sort: "newest",
        tagId: [tagId(3), tagId(2)],
      }),
    );

    await fireEvent.press(screen.getByRole("checkbox", { name: "テストタグ3" }));
    await fireEvent.press(screen.getByRole("checkbox", { name: "テストタグ2" }));

    await waitFor(() => expect(lastQuery(listCircles)).toEqual({ sort: "newest" }));
    expect(lastQuery(listCircles)).not.toHaveProperty("tagId");
  });

  it("combines tags with the keyword, official status, circle type and sort", async () => {
    const { api, listCircles } = setup();

    await renderWithApi(<SearchScreen />, api);
    await fireEvent.press(await screen.findByRole("checkbox", { name: "テストタグ1" }));
    await fireEvent.press(screen.getByRole("checkbox", { name: "テストタグ2" }));
    await fireEvent.press(screen.getByRole("checkbox", { name: "公認" }));
    await fireEvent.press(screen.getByRole("checkbox", { name: "部活" }));
    await fireEvent.press(screen.getByRole("radio", { name: "お気に入り数順" }));
    await typeKeyword("軽音");
    await settleDebounce();

    await waitFor(() =>
      expect(lastQuery(listCircles)).toEqual({
        circleType: ["club"],
        officialStatus: ["official"],
        q: "軽音",
        sort: "most_favorited",
        tagId: [tagId(1), tagId(2)],
      }),
    );

    // The other conditions survive a change of the tag selection.
    await fireEvent.press(screen.getByRole("checkbox", { name: "テストタグ1" }));
    await waitFor(() =>
      expect(lastQuery(listCircles)).toEqual({
        circleType: ["club"],
        officialStatus: ["official"],
        q: "軽音",
        sort: "most_favorited",
        tagId: [tagId(2)],
      }),
    );
  });

  it("discards the cursor and searches from the first page when the tags change", async () => {
    const { api, listCircles } = setup();
    listCircles
      .mockReset()
      .mockResolvedValueOnce(
        makeListResponse({ items: [makeCircle(1)], nextCursor: OPAQUE_CURSOR, totalCount: 40 }),
      )
      .mockResolvedValueOnce(makeListResponse({ items: [makeCircle(2)], totalCount: 3 }));

    await renderWithApi(<SearchScreen />, api);
    await screen.findByText("テストサークル1");
    await fireEvent.press(await screen.findByRole("checkbox", { name: "テストタグ1" }));

    expect(await screen.findByText("テストサークル2")).toBeTruthy();
    expect(screen.queryByText("テストサークル1")).toBeNull();
    expect(listCircles).toHaveBeenCalledTimes(2);
    expect(listCircles.mock.calls[1]?.[0]).toEqual({ sort: "newest", tagId: [tagId(1)] });
    expect(listCircles.mock.calls[1]?.[0]).not.toHaveProperty("cursor");
    expect(screen.getByText("該当 3 件")).toBeTruthy();
  });

  it("sends the cursor unchanged together with tagId when loading more", async () => {
    const { api, listCircles } = setup();
    listCircles
      .mockReset()
      .mockResolvedValueOnce(makeListResponse({ items: [makeCircle(9)] }))
      .mockResolvedValueOnce(
        makeListResponse({ items: [makeCircle(1)], nextCursor: OPAQUE_CURSOR }),
      )
      .mockResolvedValueOnce(makeListResponse({ items: [makeCircle(2)] }));

    await renderWithApi(<SearchScreen />, api);
    await screen.findByText("テストサークル9");
    await fireEvent.press(await screen.findByRole("checkbox", { name: "テストタグ2" }));
    await screen.findByText("テストサークル1");
    await act(async () => {
      fireEvent(screen.getByTestId("circle-list"), "endReached");
    });

    expect(await screen.findByText("テストサークル2")).toBeTruthy();
    expect(listCircles.mock.calls[2]?.[0]).toEqual({
      cursor: OPAQUE_CURSOR,
      sort: "newest",
      tagId: [tagId(2)],
    });
  });

  it("shows the empty-result guidance when the tags match no circle, and clears the tags with it", async () => {
    const { api, listCircles } = setup();
    listCircles
      .mockReset()
      .mockResolvedValueOnce(makeListResponse({ items: [makeCircle(1)] }))
      .mockResolvedValueOnce(makeListResponse({ items: [], totalCount: 0 }))
      .mockResolvedValueOnce(makeListResponse({ items: [makeCircle(1)] }));

    await renderWithApi(<SearchScreen />, api);
    await screen.findByText("テストサークル1");
    await fireEvent.press(await screen.findByRole("checkbox", { name: "テストタグ1" }));

    expect(await screen.findByText("条件に合うサークルが見つかりません")).toBeTruthy();
    await fireEvent.press(screen.getByRole("button", { name: "検索条件を解除" }));

    expect(await screen.findByText("テストサークル1")).toBeTruthy();
    expect(lastQuery(listCircles)).toEqual({ sort: "newest" });
    expect(screen.getByRole("checkbox", { name: "テストタグ1", checked: false })).toBeTruthy();
  });

  it("treats a 200 with no tags as normal: no tag section, and the list works", async () => {
    const { api, listCircles, listTags } = setup([]);

    await renderWithApi(<SearchScreen />, api);

    expect(await screen.findByText("テストサークル1")).toBeTruthy();
    await waitFor(() => expect(listTags).toHaveBeenCalledTimes(1));
    expect(screen.queryByText("タグ")).toBeNull();
    expect(screen.queryByText("タグを読み込めませんでした")).toBeNull();
    expect(screen.queryByRole("button", { name: "タグの読み込みを再試行" })).toBeNull();

    await fireEvent.press(screen.getByRole("checkbox", { name: "公認" }));
    await waitFor(() =>
      expect(lastQuery(listCircles)).toEqual({ officialStatus: ["official"], sort: "newest" }),
    );
  });

  it.each([
    ["offline", networkFailure()],
    ["a 503", problemFailure(503, "SERVICE_UNAVAILABLE")],
  ])("keeps the circle search working when the tag API fails (%s)", async (_name, failure) => {
    const { api, listCircles, listTags } = setup();
    listTags.mockReset().mockRejectedValue(failure);

    await renderWithApi(<SearchScreen />, api);

    expect(await screen.findByText("テストサークル1")).toBeTruthy();
    expect(await screen.findByText("タグを読み込めませんでした")).toBeTruthy();
    // Neither a full-screen error nor an empty result.
    expect(screen.queryByText("条件に合うサークルが見つかりません")).toBeNull();
    expect(screen.queryByText("オフラインです")).toBeNull();
    expect(screen.queryByText("一時的に利用できません")).toBeNull();
    expect(screen.queryByText("タグ")).toBeNull();

    await fireEvent.press(screen.getByRole("checkbox", { name: "公認" }));
    await waitFor(() =>
      expect(lastQuery(listCircles)).toEqual({ officialStatus: ["official"], sort: "newest" }),
    );
    expect(screen.getByText("テストサークル1")).toBeTruthy();
  });

  it("offers the tags after a retry of the failed tag load", async () => {
    const { api, listTags } = setup();
    listTags
      .mockReset()
      .mockRejectedValueOnce(networkFailure())
      .mockResolvedValueOnce(makeTagResponse({ items: [makeTag(1)] }));

    await renderWithApi(<SearchScreen />, api);
    await fireEvent.press(
      await screen.findByRole("button", { name: "タグの読み込みを再試行" }),
    );

    expect(await screen.findByRole("checkbox", { name: "テストタグ1" })).toBeTruthy();
    expect(screen.queryByText("タグを読み込めませんでした")).toBeNull();
  });

  it("keeps a failed tag refresh from touching the tags or the list on screen", async () => {
    const { api, listTags } = setup();

    await renderWithApi(<SearchScreen />, api);
    await screen.findByRole("checkbox", { name: "テストタグ1" });
    listTags.mockRejectedValue(networkFailure());
    await pullToRefresh();

    expect(await screen.findByText("テストサークル1")).toBeTruthy();
    expect(screen.getByRole("checkbox", { name: "テストタグ1" })).toBeTruthy();
    expect(screen.queryByText("タグを読み込めませんでした")).toBeNull();
  });

  it("cancels the tag request on leaving the screen and ignores its late response", async () => {
    const { api, listTags } = setup();
    const pending = deferred<ListTagsResponse>();
    listTags.mockReset().mockReturnValue(pending.promise);

    const view = await renderWithApi(<SearchScreen />, api);
    await screen.findByText("テストサークル1");
    const signal = listTags.mock.calls[0]?.[1]?.signal as AbortSignal;
    expect(signal.aborted).toBe(false);

    await view.unmount();
    expect(signal.aborted).toBe(true);

    const errorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
    await act(async () => {
      pending.resolve(makeTagResponse({ items: [makeTag(1)] }));
    });
    expect(errorSpy).not.toHaveBeenCalled();
    errorSpy.mockRestore();
  });

  it("shows only the newest tag response when a refresh overtakes an earlier load", async () => {
    const { api, listTags } = setup();
    const first = deferred<ListTagsResponse>();
    const second = deferred<ListTagsResponse>();
    listTags.mockReset().mockReturnValueOnce(first.promise).mockReturnValueOnce(second.promise);

    await renderWithApi(<SearchScreen />, api);
    await screen.findByText("テストサークル1");
    await pullToRefresh();

    await act(async () => {
      second.resolve(makeTagResponse({ items: [makeTag(2)] }));
    });
    await act(async () => {
      first.resolve(makeTagResponse({ items: [makeTag(1)] }));
    });

    expect(await screen.findByRole("checkbox", { name: "テストタグ2" })).toBeTruthy();
    expect(screen.queryByRole("checkbox", { name: "テストタグ1" })).toBeNull();
  });

  it("keeps searching a selected tag that was deactivated, and never offers it again", async () => {
    const { api, listCircles, listTags } = setup();

    await renderWithApi(<SearchScreen />, api);
    await fireEvent.press(await screen.findByRole("checkbox", { name: "テストタグ1" }));
    await waitFor(() =>
      expect(lastQuery(listCircles)).toEqual({ sort: "newest", tagId: [tagId(1)] }),
    );
    const callsBefore = listCircles.mock.calls.length;

    // The server deactivates tag 1: it leaves the catalog.
    listTags.mockResolvedValue(makeTagResponse({ items: [makeTag(2), makeTag(3)] }));
    await pullToRefresh();
    await screen.findByRole("checkbox", { name: "テストタグ3" });

    // Still shown and still selected, so the active condition stays visible and clearable ...
    expect(screen.getByRole("checkbox", { name: "テストタグ1", checked: true })).toBeTruthy();
    // ... and the search keeps the existing tagId (DEC-068 H5) instead of silently widening.
    for (const [query] of listCircles.mock.calls.slice(callsBefore)) {
      expect(query).toEqual({ sort: "newest", tagId: [tagId(1)] });
    }

    // Choices keep the catalog first, then the retained selection.
    const labels = screen
      .getAllByRole("checkbox")
      .map((chip) => chip.props.accessibilityLabel)
      .filter((label: string) => label.startsWith("テストタグ"));
    expect(labels).toEqual(["テストタグ2", "テストタグ3", "テストタグ1"]);

    // Once cleared it is gone and cannot be selected again.
    await fireEvent.press(screen.getByRole("checkbox", { name: "テストタグ1" }));
    expect(screen.queryByRole("checkbox", { name: "テストタグ1" })).toBeNull();
    await waitFor(() => expect(lastQuery(listCircles)).toEqual({ sort: "newest" }));
  });

  it("does not offer a tag the catalog never contained", async () => {
    const { api } = setup([makeTag(2)]);

    await renderWithApi(<SearchScreen />, api);
    await screen.findByRole("checkbox", { name: "テストタグ2" });

    expect(screen.queryByRole("checkbox", { name: "テストタグ1" })).toBeNull();
  });
});

