import { render } from "@testing-library/react-native";

import HomeScreen from "../src/app/(tabs)/index";

describe("HomeScreen", () => {
  it("identifies the mobile product", async () => {
    const { getByText } = await render(<HomeScreen />);

    expect(getByText("サークルを見つけよう")).toBeTruthy();
    expect(getByText("公開サークルを見つけるホーム画面です。")).toBeTruthy();
  });
});
