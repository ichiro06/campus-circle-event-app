import { act, fireEvent, screen } from "@testing-library/react-native";
import { router, useLocalSearchParams } from "expo-router";
import { AccessibilityInfo } from "react-native";

import { ApiClientError } from "../src/api";
import * as detailHook from "../src/circles/use-circle-detail";
import { CirclesApiProvider } from "../src/circles/circles-api-context";

import CircleDetailScreen from "../src/app/circles/[circleId]";
import {
  circleId,
  createMockApi,
  makeDetail,
  makeDetailResponse,
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

function deferred<Value>() {
  let resolve: (value: Value) => void = () => {};
  let reject: (reason: unknown) => void = () => {};
  const promise = new Promise<Value>((res, rej) => { resolve = res; reject = rej; });
  return { promise, resolve, reject };
}

const mockParams = useLocalSearchParams as jest.Mock;

describe("CircleDetailScreen", () => {
  let announce: jest.SpyInstance;

  function expectAnnouncements(...messages: string[]) {
    expect(announce.mock.calls).toEqual(messages.map((message) => [message]));
  }

  beforeEach(() => {
    announce = jest.spyOn(AccessibilityInfo, "announceForAccessibility");
    mockParams.mockReturnValue({ circleId: circleId(1) });
    jest.mocked(router.canGoBack).mockReturnValue(true);
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.clearAllMocks();
    jest.restoreAllMocks();
  });

  it("requests the Circle named by the route", async () => {
    const { api, getCircle } = createMockApi();
    getCircle.mockResolvedValue(makeDetailResponse(makeDetail(1)));

    await renderWithApi(<CircleDetailScreen />, api);
    await screen.findByText("テストサークル1");

    expect(getCircle).toHaveBeenCalledTimes(1);
    expect(getCircle.mock.calls[0]?.[0]).toBe(circleId(1));
  });

  it("shows every public field the API provides", async () => {
    const { api, getCircle } = createMockApi();
    getCircle.mockResolvedValue(makeDetailResponse(makeDetail(1)));

    await renderWithApi(<CircleDetailScreen />, api);

    expect(await screen.findByText("テストサークル1")).toBeTruthy();
    expect(screen.getByText("キャッチコピー1")).toBeTruthy();
    expect(screen.getByText("主な活動内容1")).toBeTruthy();
    expect(screen.getByText("詳しい説明1")).toBeTruthy();
    expect(screen.getByText("公認")).toBeTruthy();
    expect(screen.getByText("サークル")).toBeTruthy();
    expect(screen.getByText("音楽")).toBeTruthy();
    expect(screen.getByText("募集中")).toBeTruthy();
    expect(screen.getByText("法政大学 市ヶ谷")).toBeTruthy();
    expect(screen.getByText("東京都千代田区・学生会館・最寄駅 市ヶ谷")).toBeTruthy();
    expect(screen.getByText("月曜日 夕方（18:00〜20:00）")).toBeTruthy();
    expect(screen.getByText("31〜80人")).toBeTruthy();
    expect(screen.getByText("週1回")).toBeTruthy();
    expect(screen.getByText("年1回")).toBeTruthy();
    expect(screen.getByText("年会費")).toBeTruthy();
    expect(screen.getByText("3,000円")).toBeTruthy();
    expect(screen.getByText("新入生は無料")).toBeTruthy();
    expect(screen.getByText("#初心者歓迎  #ライブ")).toBeTruthy();
  });

  it("labels the ratings and gender balance as the group's self-report", async () => {
    const { api, getCircle } = createMockApi();
    getCircle.mockResolvedValue(makeDetailResponse(makeDetail(1)));

    await renderWithApi(<CircleDetailScreen />, api);
    await screen.findByText("テストサークル1");

    expect(screen.getByText("団体による自己申告")).toBeTruthy();
    expect(screen.getByText("飲み会の頻度")).toBeTruthy();
    expect(screen.getByText("賑やかさ")).toBeTruthy();
    expect(screen.getByText("活動の本気度")).toBeTruthy();
    expect(screen.getByText("出席自由度")).toBeTruthy();
    expect(screen.getByText("ガクチカにつながる度")).toBeTruthy();
    expect(screen.getByText("2 / 5")).toBeTruthy();
    expect(screen.getByText("男女比（団体による自己申告）")).toBeTruthy();
    expect(screen.getByText("概ね均衡")).toBeTruthy();
    expect(
      screen.getByLabelText(/飲み会の頻度、5段階中 2。1はなし、5は週1回以上/),
    ).toBeTruthy();
  });

  it("treats null values as unanswered instead of inventing data", async () => {
    const { api, getCircle } = createMockApi();
    getCircle.mockResolvedValue(
      makeDetailResponse(
        makeDetail(1, {
          activityFrequencyCode: null,
          activityLocations: [],
          activitySchedules: [],
          attendanceFlexibilityRating: null,
          campFrequencyCode: null,
          careerOpportunityRating: null,
          commitmentRating: null,
          costs: [],
          drinkingFrequencyRating: null,
          genderBalanceCode: null,
          livelinessRating: null,
          memberCountBand: null,
          tags: [],
          universities: [],
        }),
      ),
    );

    await renderWithApi(<CircleDetailScreen />, api);
    await screen.findByText("テストサークル1");

    // five ratings + gender balance + member count + frequency + camp
    expect(screen.getAllByText("未回答")).toHaveLength(9);
    expect(screen.getAllByText("未設定")).toHaveLength(3);
    expect(screen.getByText("費用情報は登録されていません。")).toBeTruthy();
    expect(screen.queryByText(/ \/ 5$/)).toBeNull();
  });

  it("formats open-ended and ranged costs", async () => {
    const { api, getCircle } = createMockApi();
    getCircle.mockResolvedValue(
      makeDetailResponse(
        makeDetail(1, {
          costs: [
            { costType: "annual", amountMinYen: 0, amountMaxYen: 0, label: "年会費", note: null },
            {
              costType: "per_event",
              amountMinYen: 1000,
              amountMaxYen: 3000,
              label: "合宿",
              note: null,
            },
          ],
        }),
      ),
    );

    await renderWithApi(<CircleDetailScreen />, api);

    expect(await screen.findByText("0円")).toBeTruthy();
    expect(screen.getByText("合宿（参加ごとの費用）")).toBeTruthy();
    expect(screen.getByText("1,000円〜3,000円")).toBeTruthy();
  });

  it("shows nothing for 300ms and then a skeleton while loading", async () => {
    jest.useFakeTimers();
    const { api, getCircle } = createMockApi();
    getCircle.mockReturnValue(new Promise(() => {}));

    await renderWithApi(<CircleDetailScreen />, api);
    expect(screen.queryByRole("progressbar")).toBeNull();

    await act(async () => {
      jest.advanceTimersByTime(300);
    });
    expect(screen.getByRole("progressbar")).toBeTruthy();
  });

  it("does not claim why a 404 happened and offers a way back to the list", async () => {
    const { api, getCircle } = createMockApi();
    getCircle.mockRejectedValue(problemFailure(404, "NOT_FOUND"));

    await renderWithApi(<CircleDetailScreen />, api);

    expect(await screen.findByText("現在このサークル情報を表示できません。")).toBeTruthy();
    expect(screen.queryByText(/削除|非公開|存在しない|SELECT|internal/)).toBeNull();
    // Retrying the same request cannot change a 404.
    expect(screen.queryByRole("button", { name: "再試行" })).toBeNull();

    await fireEvent.press(screen.getByRole("button", { name: "一覧へ戻る" }));
    expect(router.back).toHaveBeenCalledTimes(1);
  });

  it("falls back to the Home route when there is no history to go back to", async () => {
    jest.mocked(router.canGoBack).mockReturnValue(false);
    const { api, getCircle } = createMockApi();
    getCircle.mockRejectedValue(problemFailure(404, "NOT_FOUND"));

    await renderWithApi(<CircleDetailScreen />, api);
    await fireEvent.press(await screen.findByRole("button", { name: "一覧へ戻る" }));

    expect(router.replace).toHaveBeenCalledWith("/");
  });

  it("shows a retryable error with the request ID and recovers", async () => {
    const { api, getCircle } = createMockApi();
    getCircle
      .mockRejectedValueOnce(problemFailure(503, "SERVICE_UNAVAILABLE"))
      .mockResolvedValueOnce(makeDetailResponse(makeDetail(1)));

    await renderWithApi(<CircleDetailScreen />, api);

    expect(await screen.findByText("一時的に利用できません")).toBeTruthy();
    expect(screen.getByText(`問い合わせID: ${REQUEST_ID}`)).toBeTruthy();

    await fireEvent.press(screen.getByRole("button", { name: "再試行" }));
    expect(await screen.findByText("テストサークル1")).toBeTruthy();
  });

  it("shows the offline state when the network fails", async () => {
    const { api, getCircle } = createMockApi();
    getCircle.mockRejectedValue(networkFailure());

    await renderWithApi(<CircleDetailScreen />, api);

    expect(await screen.findByText("オフラインです")).toBeTruthy();
    expect(screen.getByRole("button", { name: "再試行" })).toBeTruthy();
  });

  it("handles a missing route parameter without calling the API", async () => {
    mockParams.mockReturnValue({});
    const { api, getCircle } = createMockApi();

    await renderWithApi(<CircleDetailScreen />, api);

    expect(await screen.findByText("サークルIDを確認できませんでした。")).toBeTruthy();
    expect(getCircle).not.toHaveBeenCalled();
  });
  async function pullToRefresh() {
    await act(async () => {
      screen.getByTestId("circle-detail-scroll").props.refreshControl.props.onRefresh();
    });
  }

  it("refreshes the current ID, keeps data while pending and announces completion", async () => {
    const pending = deferred<ReturnType<typeof makeDetailResponse>>();
    const { api, getCircle } = createMockApi();
    getCircle.mockResolvedValueOnce(makeDetailResponse(makeDetail(1)))
      .mockReturnValueOnce(pending.promise);
    await renderWithApi(<CircleDetailScreen />, api);
    await screen.findByText("テストサークル1");

    await pullToRefresh();
    expect(getCircle).toHaveBeenLastCalledWith(circleId(1), expect.anything());
    expect(screen.getByText("テストサークル1")).toBeTruthy();
    expect(screen.getByTestId("circle-detail-scroll").props.refreshControl.props.refreshing).toBe(true);
    expect(screen.queryByRole("progressbar")).toBeNull();
    expect(screen.getByRole("button", { name: "情報を更新中です" })).toBeDisabled();
    expectAnnouncements("情報を更新中です");

    await act(async () => pending.resolve(makeDetailResponse(makeDetail(1, { displayName: "更新したサークル" }))));
    expect(await screen.findByText("更新したサークル")).toBeTruthy();
    expect(screen.getByTestId("circle-detail-scroll").props.refreshControl.props.refreshing).toBe(false);
    expectAnnouncements("情報を更新中です", "情報を更新しました");
  });

  it.each([
    ["server", () => problemFailure(503, "SERVICE_UNAVAILABLE"), "一時的に利用できません"],
    ["offline", networkFailure, "オフラインです"],
  ])("keeps the last data and timestamp after a %s refresh failure, then retries", async (_, failure, title) => {
    const { api, getCircle } = createMockApi();
    getCircle.mockResolvedValueOnce(makeDetailResponse(makeDetail(1)))
      .mockRejectedValueOnce(failure())
      .mockResolvedValueOnce(makeDetailResponse(makeDetail(1, { displayName: "復旧したサークル" })));
    await renderWithApi(<CircleDetailScreen />, api);
    await screen.findByText("テストサークル1");
    await pullToRefresh();

    expect(await screen.findByText(title)).toBeTruthy();
    expect(screen.getByText("テストサークル1")).toBeTruthy();
    expect(screen.getByText(/最終更新/)).toBeTruthy();
    expect(screen.getByTestId("circle-detail-scroll").props.refreshControl.props.refreshing).toBe(false);
    await fireEvent.press(screen.getByRole("button", { name: "再試行" }));
    expect(await screen.findByText("復旧したサークル")).toBeTruthy();
    expect(screen.queryByText(title)).toBeNull();
  });

  it("offers an ordinary refresh button without requiring a gesture", async () => {
    const pending = deferred<ReturnType<typeof makeDetailResponse>>();
    const { api, getCircle } = createMockApi();
    getCircle.mockResolvedValueOnce(makeDetailResponse(makeDetail(1)))
      .mockReturnValueOnce(pending.promise);
    await renderWithApi(<CircleDetailScreen />, api);
    await fireEvent.press(await screen.findByRole("button", { name: "情報を更新" }));
    expectAnnouncements("情報を更新中です");
    await act(async () => pending.resolve(makeDetailResponse(makeDetail(1, { headline: "新しい紹介" }))));
    expect(await screen.findByText("新しい紹介")).toBeTruthy();
    expectAnnouncements("情報を更新中です", "情報を更新しました");
    expect(getCircle).toHaveBeenCalledTimes(2);
  });

  it("ignores repeated pulls and retry while the current read is pending", async () => {
    const pending = deferred<ReturnType<typeof makeDetailResponse>>();
    const { api, getCircle } = createMockApi();
    getCircle.mockResolvedValueOnce(makeDetailResponse(makeDetail(1)))
      .mockReturnValueOnce(pending.promise);
    await renderWithApi(<CircleDetailScreen />, api);
    await screen.findByText("テストサークル1");
    await pullToRefresh();
    await pullToRefresh();
    expect(getCircle).toHaveBeenCalledTimes(2);
    expectAnnouncements("情報を更新中です");
    await act(async () => pending.resolve(makeDetailResponse(makeDetail(1))));
    expectAnnouncements("情報を更新中です", "情報を更新しました");
  });

  it("aborts a pending refresh when unmounted and fetches anew on return", async () => {
    const pending = deferred<ReturnType<typeof makeDetailResponse>>();
    const { api, getCircle } = createMockApi();
    getCircle.mockResolvedValueOnce(makeDetailResponse(makeDetail(1)))
      .mockReturnValueOnce(pending.promise)
      .mockResolvedValueOnce(makeDetailResponse(makeDetail(1, { displayName: "戻った画面" })));
    const rendered = await renderWithApi(<CircleDetailScreen />, api);
    await screen.findByText("テストサークル1");
    await pullToRefresh();
    const signal = getCircle.mock.calls[1]?.[1]?.signal;
    await rendered.unmount();
    expect(signal?.aborted).toBe(true);
    await renderWithApi(<CircleDetailScreen />, api);
    await screen.findByText("戻った画面");
    await act(async () => pending.resolve(makeDetailResponse(makeDetail(1, { displayName: "古い応答" }))));
    expect(screen.queryByText("古い応答")).toBeNull();
    expect(screen.getByText("戻った画面")).toBeTruthy();
    expectAnnouncements("情報を更新中です");
  });

  it("isolates another Circle ID from late refresh responses", async () => {
    const observedDetail = jest.spyOn(detailHook, "useCircleDetail");
    const nextRefresh = deferred<ReturnType<typeof makeDetailResponse>>();
    const pending = deferred<ReturnType<typeof makeDetailResponse>>();
    const { api, getCircle } = createMockApi();
    getCircle.mockResolvedValueOnce(makeDetailResponse(makeDetail(1)))
      .mockReturnValueOnce(pending.promise)
      .mockResolvedValueOnce(makeDetailResponse(makeDetail(2)))
      .mockReturnValueOnce(nextRefresh.promise);
    const rendered = await renderWithApi(<CircleDetailScreen />, api);
    await screen.findByText("テストサークル1");
    await pullToRefresh();
    const signal = getCircle.mock.calls[1]?.[1]?.signal;
    mockParams.mockReturnValue({ circleId: circleId(2) });
    await rendered.rerender(<CirclesApiProvider value={api}><CircleDetailScreen /></CirclesApiProvider>);
    expect(await screen.findByText("テストサークル2")).toBeTruthy();
    expect(signal?.aborted).toBe(true);
    await act(async () => pending.resolve(makeDetailResponse(makeDetail(1))));
    expect(screen.queryByText("テストサークル1")).toBeNull();
    expectAnnouncements("情報を更新中です");
    await pullToRefresh();
    expect(getCircle).toHaveBeenCalledTimes(4);
    expect(getCircle).toHaveBeenLastCalledWith(circleId(2), expect.anything());
    expectAnnouncements("情報を更新中です", "情報を更新中です");
    await act(async () => nextRefresh.resolve(makeDetailResponse(makeDetail(2, {
      headline: "切替先の更新済み情報",
    }))));
    expect(await screen.findByText("切替先の更新済み情報")).toBeTruthy();
    expect(screen.queryByText("テストサークル1")).toBeNull();
    expect(screen.queryByRole("alert")).toBeNull();
    expect(observedDetail.mock.results.at(-1)?.value).toMatchObject({
      error: null,
      isLoading: false,
      isRefreshing: false,
    });
    const updateButton = screen.getByRole("button", { name: "情報を更新" });
    expect(updateButton).toBeEnabled();
    expect(updateButton.props.accessibilityState.busy).toBe(false);
    expect(screen.getByTestId("circle-detail-scroll").props.refreshControl.props.refreshing).toBe(false);
    expectAnnouncements("情報を更新中です", "情報を更新中です", "情報を更新しました");
  });

  it("announces a failed refresh exactly once at start and completion", async () => {
    const pending = deferred<ReturnType<typeof makeDetailResponse>>();
    const { api, getCircle } = createMockApi();
    getCircle.mockResolvedValueOnce(makeDetailResponse(makeDetail(1)))
      .mockReturnValueOnce(pending.promise);
    await renderWithApi(<CircleDetailScreen />, api);
    await screen.findByText("テストサークル1");
    await pullToRefresh();
    expectAnnouncements("情報を更新中です");
    await act(async () => pending.reject(networkFailure()));
    expect(await screen.findByText("オフラインです")).toBeTruthy();
    expect(screen.getByText("テストサークル1")).toBeTruthy();
    expectAnnouncements("情報を更新中です", "情報を更新できませんでした");
  });

  it.each(["success", "failure"] as const)("announces retained-data retry start and %s", async (outcome) => {
    const failedRefresh = deferred<ReturnType<typeof makeDetailResponse>>();
    const retry = deferred<ReturnType<typeof makeDetailResponse>>();
    const { api, getCircle } = createMockApi();
    getCircle.mockResolvedValueOnce(makeDetailResponse(makeDetail(1)))
      .mockReturnValueOnce(failedRefresh.promise)
      .mockReturnValueOnce(retry.promise);
    await renderWithApi(<CircleDetailScreen />, api);
    await screen.findByText("テストサークル1");
    await pullToRefresh();
    await act(async () => failedRefresh.reject(networkFailure()));
    expectAnnouncements("情報を更新中です", "情報を更新できませんでした");
    announce.mockClear();

    await fireEvent.press(screen.getByRole("button", { name: "再試行" }));
    expectAnnouncements("情報を更新中です");
    expect(screen.getByText("テストサークル1")).toBeTruthy();
    expect(screen.getByRole("button", { name: "情報を更新中です" })).toBeDisabled();
    // Retry is still distinct from an explicit refresh.
    expect(screen.getByTestId("circle-detail-scroll").props.refreshControl.props.refreshing).toBe(false);
    await act(async () => {
      if (outcome === "success") {
        retry.resolve(makeDetailResponse(makeDetail(1, { headline: "再試行で更新" })));
      } else {
        retry.reject(problemFailure(503, "SERVICE_UNAVAILABLE"));
      }
    });
    if (outcome === "success") {
      expect(await screen.findByText("再試行で更新")).toBeTruthy();
      expect(screen.queryByRole("alert")).toBeNull();
    } else {
      expect(await screen.findByText("一時的に利用できません")).toBeTruthy();
    }
    expect(screen.getByRole("button", { name: "情報を更新" })).toBeEnabled();
    expectAnnouncements("情報を更新中です", outcome === "success"
      ? "情報を更新しました" : "情報を更新できませんでした");
  });

  it("does not duplicate initial Skeleton notifications", async () => {
    jest.useFakeTimers();
    const pending = deferred<ReturnType<typeof makeDetailResponse>>();
    const { api, getCircle } = createMockApi();
    getCircle.mockReturnValue(pending.promise);
    await renderWithApi(<CircleDetailScreen />, api);
    expectAnnouncements();
    await act(async () => jest.advanceTimersByTime(300));
    expect(screen.getByRole("progressbar")).toBeTruthy();
    expectAnnouncements("読み込み中です");
    await act(async () => pending.resolve(makeDetailResponse(makeDetail(1))));
    expect(screen.getByText("テストサークル1")).toBeTruthy();
    expectAnnouncements("読み込み中です", "読み込みが終わりました");
  });

  it("does not announce successful completion for a cancelled re-fetch", async () => {
    const pending = deferred<ReturnType<typeof makeDetailResponse>>();
    const { api, getCircle } = createMockApi();
    getCircle.mockResolvedValueOnce(makeDetailResponse(makeDetail(1)))
      .mockReturnValueOnce(pending.promise);
    await renderWithApi(<CircleDetailScreen />, api);
    await screen.findByText("テストサークル1");
    await pullToRefresh();
    await act(async () => pending.reject(new ApiClientError({ kind: "cancelled" })));
    expect(screen.getByRole("button", { name: "情報を更新" })).toBeEnabled();
    expectAnnouncements("情報を更新中です");
  });

  it("does not repeat retry notifications for duplicate operations or unrelated renders", async () => {
    const observedDetail = jest.spyOn(detailHook, "useCircleDetail");
    const retry = deferred<ReturnType<typeof makeDetailResponse>>();
    const { api, getCircle } = createMockApi();
    getCircle.mockResolvedValueOnce(makeDetailResponse(makeDetail(1)))
      .mockRejectedValueOnce(networkFailure())
      .mockReturnValueOnce(retry.promise);
    const rendered = await renderWithApi(<CircleDetailScreen />, api);
    await screen.findByText("テストサークル1");
    await pullToRefresh();
    const onRetry = observedDetail.mock.results.at(-1)?.value.retry;
    announce.mockClear();
    await act(async () => { onRetry(); onRetry(); });
    await pullToRefresh();
    await rendered.rerender(<CirclesApiProvider value={api}><CircleDetailScreen /></CirclesApiProvider>);
    expect(getCircle).toHaveBeenCalledTimes(3);
    expectAnnouncements("情報を更新中です");
    expect(screen.getByTestId("circle-detail-scroll").props.refreshControl.props.refreshing).toBe(false);
    await act(async () => retry.resolve(makeDetailResponse(makeDetail(1))));
    expectAnnouncements("情報を更新中です", "情報を更新しました");
  });

});
