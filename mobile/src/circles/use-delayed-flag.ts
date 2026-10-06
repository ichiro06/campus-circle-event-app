import { useEffect, useState } from "react";

/** docs/screen-flow.md 5.1: skeletons appear only for work that exceeds 300ms. */
export const LOADING_INDICATOR_DELAY_MS = 300;

export function useDelayedFlag(
  active: boolean,
  delayMs: number = LOADING_INDICATOR_DELAY_MS,
): boolean {
  const [elapsed, setElapsed] = useState(false);

  useEffect(() => {
    if (!active) {
      return undefined;
    }

    const timeoutId = setTimeout(() => setElapsed(true), delayMs);

    return () => {
      clearTimeout(timeoutId);
      setElapsed(false);
    };
  }, [active, delayMs]);

  return active && elapsed;
}
