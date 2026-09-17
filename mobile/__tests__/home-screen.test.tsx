import { render } from "@testing-library/react-native";

import HomeScreen from "../src/app/index";

describe("HomeScreen", () => {
  it("identifies the mobile product", async () => {
    const { getByText } = await render(<HomeScreen />);

    expect(getByText("サークルを見つけよう")).toBeTruthy();
    expect(
      getByText("iOS・Androidアプリの開発環境が整いました。"),
    ).toBeTruthy();
  });
});
