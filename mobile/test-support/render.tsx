import { render } from "@testing-library/react-native";
import type { ReactElement } from "react";

import type { CirclesApi } from "../src/api";
import { CirclesApiProvider } from "../src/circles/circles-api-context";

export function renderWithApi(ui: ReactElement, api: CirclesApi) {
  return render(<CirclesApiProvider value={api}>{ui}</CirclesApiProvider>);
}
