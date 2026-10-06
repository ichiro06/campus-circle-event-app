import { useEffect, useMemo, useSyncExternalStore } from "react";

import { CircleDetailStore, type CircleDetailSnapshot } from "./circle-detail-store";
import { useCirclesApi } from "./circles-api-context";

export interface CircleDetailState extends CircleDetailSnapshot {
  retry: () => void;
}

const NO_CIRCLE: CircleDetailSnapshot = {
  circle: null,
  isLoading: false,
  error: null,
  lastUpdatedAt: null,
};

const noopSubscribe = () => () => {};
const noSnapshot = () => NO_CIRCLE;
const noop = () => {};

export function useCircleDetail(circleId: string | undefined): CircleDetailState {
  const api = useCirclesApi();
  const store = useMemo(
    () => (circleId === undefined ? null : new CircleDetailStore(api, circleId)),
    [api, circleId],
  );

  useEffect(() => {
    store?.start();

    return () => store?.stop();
  }, [store]);

  const snapshot = useSyncExternalStore(
    store?.subscribe ?? noopSubscribe,
    store?.getSnapshot ?? noSnapshot,
  );

  return { ...snapshot, retry: store?.retry ?? noop };
}
