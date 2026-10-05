import { act, fireEvent, screen, waitFor } from "@testing-library/react-native";

import SearchScreen, { SEARCH_DEBOUNCE_MS } from "../src/app/(tabs)/search";
import {
  createMockApi,
  makeCircle,
  makeListResponse,
  problemFailure,
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
