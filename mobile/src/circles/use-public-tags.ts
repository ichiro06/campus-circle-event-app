import { useEffect, useMemo, useSyncExternalStore } from "react";

import { useCirclesApi } from "./circles-api-context";
import { TagCatalogStore, type TagCatalogStatus } from "./tag-catalog-store";
import type { PublicTag } from "./types";

export interface PublicTags {
  /** Active tags in API order. Empty until the catalog has loaded, and when none exist. */
  tags: readonly PublicTag[];
  status: TagCatalogStatus;
  /** True once a load has succeeded, which tells an empty catalog from one not yet loaded. */
  hasLoaded: boolean;
  /** Loads the catalog again, keeping the tags shown meanwhile. */
  refresh: () => void;
}

/** The public tag catalog used as the choices of the tag filter. */
export function usePublicTags(): PublicTags {
  const api = useCirclesApi();
  const store = useMemo(() => new TagCatalogStore(api), [api]);

  useEffect(() => {
    store.start();

    return () => store.stop();
  }, [store]);

  const snapshot = useSyncExternalStore(store.subscribe, store.getSnapshot);

  return {
    tags: snapshot.tags,
    status: snapshot.status,
    hasLoaded: snapshot.hasLoaded,
    refresh: store.refresh,
  };
}
