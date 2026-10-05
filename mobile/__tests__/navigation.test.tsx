import { render } from "@testing-library/react-native";
import { useLocalSearchParams } from "expo-router";

import {
  circleId,
  createMockApi,
  makeDetail,
  makeDetailResponse,
  makeListResponse,
} from "../test-support/circles";
import { renderWithApi } from "../test-support/render";

import { TAB_ROUTES } from "../src/app/(tabs)/_layout";
import FavoritesScreen from "../src/app/(tabs)/favorites";
import HomeScreen from "../src/app/(tabs)/index";
import MyPageScreen from "../src/app/(tabs)/me";
import SearchScreen from "../src/app/(tabs)/search";
import { ROOT_STACK_ROUTES } from "../src/app/_layout";
import CircleDetailScreen from "../src/app/circles/[circleId]";

jest.mock("expo-router", () => {
  const actual = jest.requireActual("expo-router");

  return {
    ...actual,
    useLocalSearchParams: jest.fn(),
  };
});

const mockUseLocalSearchParams = useLocalSearchParams as jest.Mock;

describe("mobile navigation shell", () => {
  it("defines the four formal tabs", () => {
    expect(TAB_ROUTES).toEqual([
      { name: "index", title: "ホーム" },
      { name: "search", title: "検索" },
      { name: "favorites", title: "お気に入り" },
      { name: "me", title: "マイページ" },
    ]);
  });

  it("keeps Circle detail above the tab group in the root stack", () => {
    expect(ROOT_STACK_ROUTES).toEqual({
      circleDetail: "circles/[circleId]",
      tabs: "(tabs)",
    });
  });

  it("renders the logged-out Home screen", async () => {
    const { api, listCircles } = createMockApi();
    listCircles.mockResolvedValue(makeListResponse({ items: [] }));
    const home = await renderWithApi(<HomeScreen />, api);
    expect(home.getByText("サークルを見つけよう")).toBeTruthy();
  });

  it("renders the logged-out Search screen", async () => {
    const { api, listCircles } = createMockApi();
    listCircles.mockResolvedValue(makeListResponse({ items: [] }));
    const search = await renderWithApi(<SearchScreen />, api);
    expect(search.getByText("サークルを検索")).toBeTruthy();
  });

  it("renders the login-required Favorites shell", async () => {
    const favorites = await render(<FavoritesScreen />);
    expect(
      favorites.getByText("お気に入りを見るにはログインが必要です。"),
    ).toBeTruthy();
  });

  it("renders the login-required My Page shell", async () => {
    const myPage = await render(<MyPageScreen />);
    expect(
      myPage.getByText(
        "マイページを使うにはログインまたは新規登録が必要です。",
      ),
    ).toBeTruthy();
  });

  it("loads the Circle named by the detail route parameter", async () => {
    mockUseLocalSearchParams.mockReturnValue({ circleId: circleId(1) });
    const { api, getCircle } = createMockApi();
    getCircle.mockResolvedValue(makeDetailResponse(makeDetail(1)));
    const detail = await renderWithApi(<CircleDetailScreen />, api);

    expect(await detail.findByText("テストサークル1")).toBeTruthy();
    expect(getCircle.mock.calls[0]?.[0]).toBe(circleId(1));
  });
});
