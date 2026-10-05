import { fireEvent, render, screen } from "@testing-library/react-native";

import { CircleCard } from "../src/components/circle-card";
import { circleId, makeCircle } from "../test-support/circles";

describe("CircleCard", () => {
  it("shows the required and available public fields", async () => {
    await render(<CircleCard circle={makeCircle(1)} onPress={jest.fn()} />);

    expect(screen.getByText("テストサークル1")).toBeTruthy();
    expect(screen.getByText("キャッチコピー1")).toBeTruthy();
    expect(screen.getByText("主な活動内容1")).toBeTruthy();
    expect(screen.getByText("公認")).toBeTruthy();
    expect(screen.getByText("サークル")).toBeTruthy();
    expect(screen.getByText("法政大学 市ヶ谷")).toBeTruthy();
    expect(screen.getByText("東京都千代田区・学生会館・最寄駅 市ヶ谷")).toBeTruthy();
    expect(screen.getByText("月曜日 夕方")).toBeTruthy();
    expect(screen.getByText("#初心者歓迎")).toBeTruthy();
  });

  it("shows at most the five featured tags the API provides", async () => {
    const featuredTags = Array.from({ length: 5 }, (_, index) => ({
      id: circleId(500 + index),
      name: `タグ${index}`,
      slug: `tag-${index}`,
    }));
    await render(
      <CircleCard circle={makeCircle(1, { featuredTags })} onPress={jest.fn()} />,
    );

    for (let index = 0; index < 5; index += 1) {
      expect(screen.getByText(new RegExp(`#タグ${index}`))).toBeTruthy();
    }
  });

  it("copes with empty optional collections", async () => {
    await render(
      <CircleCard
        circle={makeCircle(1, {
          activityLocations: [],
          activitySchedules: [],
          featuredTags: [],
          officialStatus: "unknown",
          universities: [],
        })}
        onPress={jest.fn()}
      />,
    );

    expect(screen.getByText("公認区分は未確認")).toBeTruthy();
    expect(screen.queryByText(/^#/)).toBeNull();
  });

  it("is one button that reports the Circle ID when pressed", async () => {
    const onPress = jest.fn();
    await render(<CircleCard circle={makeCircle(4)} onPress={onPress} />);

    await fireEvent.press(screen.getByRole("button", { name: /テストサークル4/ }));

    expect(onPress).toHaveBeenCalledWith(circleId(4));
  });

  it("describes the whole card to screen readers and meets the tap target size", async () => {
    await render(<CircleCard circle={makeCircle(1)} onPress={jest.fn()} />);

    const card = screen.getByRole("button");

    expect(card.props.accessibilityLabel).toContain("テストサークル1");
    expect(card.props.accessibilityLabel).toContain("公認、サークル");
    expect(card.props.accessibilityLabel).toContain("法政大学 市ヶ谷");
    expect(card.props.accessibilityHint).toBe("サークルの詳細を開きます");
    expect(card).toHaveStyle({ minHeight: 48 });
  });

  it("does not render favorite, report, or share controls", async () => {
    await render(<CircleCard circle={makeCircle(1)} onPress={jest.fn()} />);

    expect(screen.getAllByRole("button")).toHaveLength(1);
  });

  it("does not use color alone for the official status", async () => {
    await render(
      <CircleCard
        circle={makeCircle(1, { officialStatus: "unofficial" })}
        onPress={jest.fn()}
      />,
    );

    expect(screen.getByText("非公認")).toBeTruthy();
  });
});
