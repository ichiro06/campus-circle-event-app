import { fireEvent, render } from "@testing-library/react-native";

import {
  EmptyState,
  ErrorState,
  LoadingState,
  OfflineState,
} from "../src/components/common-states";

describe("common state presentation", () => {
  it("renders an accessible Loading state", async () => {
    const screen = await render(<LoadingState />);

    expect(screen.getByText("読み込み中です")).toBeTruthy();
    expect(screen.getByRole("progressbar")).toBeTruthy();
  });

  it("renders Empty state guidance and an optional action", async () => {
    const onAction = jest.fn();
    const screen = await render(
      <EmptyState
        actionLabel="条件を解除"
        description="条件に合うサークルがありません。"
        onAction={onAction}
        title="検索結果は0件です"
      />,
    );

    fireEvent.press(screen.getByRole("button", { name: "条件を解除" }));
    expect(onAction).toHaveBeenCalledTimes(1);
  });

  it("renders Error state request ID and an optional retry", async () => {
    const onRetry = jest.fn();
    const screen = await render(
      <ErrorState
        description="通信状態を確認してください。"
        onRetry={onRetry}
        requestId="00000000-0000-0000-0000-000000000000"
      />,
    );

    expect(
      screen.getByText(
        "問い合わせID: 00000000-0000-0000-0000-000000000000",
      ),
    ).toBeTruthy();
    fireEvent.press(screen.getByRole("button", { name: "再試行" }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("renders Offline state as presentation only", async () => {
    const screen = await render(
      <OfflineState lastUpdatedLabel="最終更新: 10分前" />,
    );

    expect(screen.getByText("オフラインです")).toBeTruthy();
    expect(screen.getByText("最終更新: 10分前")).toBeTruthy();
    expect(screen.getByRole("alert")).toBeTruthy();
  });
});
