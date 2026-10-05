import { createContext, useContext } from "react";

import { createCirclesApi, type CirclesApi } from "@/api";

const CirclesApiContext = createContext<CirclesApi | null>(null);

export const CirclesApiProvider = CirclesApiContext.Provider;

let defaultApi: CirclesApi | undefined;

/** Lazily built so importing a screen never reads the environment. */
export function useCirclesApi(): CirclesApi {
  const provided = useContext(CirclesApiContext);

  if (provided) {
    return provided;
  }

  defaultApi ??= createCirclesApi();

  return defaultApi;
}
