import type { ApiFailure, CirclesApi } from "@/api";

import { toApiFailure } from "./failure-presentation";
import type { CircleDetail } from "./types";

export interface CircleDetailSnapshot {
  circle: CircleDetail | null;
  isLoading: boolean;
  /** Only an explicit user refresh drives the native pull indicator. */
  isRefreshing: boolean;
  error: { failure: ApiFailure; occurredAt: Date } | null;
  /** Time of the last successful fetch whose data is still on screen. */
  lastUpdatedAt: Date | null;
}

const INITIAL_SNAPSHOT: CircleDetailSnapshot = {
  circle: null,
  isLoading: true,
  isRefreshing: false,
  error: null,
  lastUpdatedAt: null,
};

/** Loads one public Circle. A different Circle ID means a different store. */
export class CircleDetailStore {
  private snapshot: CircleDetailSnapshot = INITIAL_SNAPSHOT;
  private readonly listeners = new Set<() => void>();
  private controller: AbortController | null = null;
  private generation = 0;
  private active = false;

  constructor(
    private readonly api: CirclesApi,
    private readonly circleId: string,
  ) {}

  subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);

    return () => {
      this.listeners.delete(listener);
    };
  };

  getSnapshot = (): CircleDetailSnapshot => this.snapshot;

  /** Safe to call again after stop(): it refetches only if nothing was loaded yet. */
  start(): void {
    this.active = true;
    if (this.snapshot.lastUpdatedAt === null && this.snapshot.error === null) {
      void this.load();
    }
  }

  stop(): void {
    this.active = false;
    this.generation += 1;
    this.controller?.abort();
    this.controller = null;
    this.update({ isLoading: false, isRefreshing: false });
  }

  /** Retry the failed read without pretending it was a pull gesture. */
  retry = (): void => {
    void this.load();
  };

  refresh = (): void => {
    void this.load(true);
  };

  private update(changes: Partial<CircleDetailSnapshot>): void {
    this.snapshot = { ...this.snapshot, ...changes };

    for (const listener of this.listeners) {
      listener();
    }
  }

  private async load(isRefreshing = false): Promise<void> {
    // Coalesce start, retry and refresh while any read is in flight.
    if (!this.active || this.controller !== null) {
      return;
    }

    this.controller = new AbortController();
    this.generation += 1;
    const generation = this.generation;
    const { signal } = this.controller;

    this.update({ isLoading: true, isRefreshing, error: null });

    try {
      const response = await this.api.getCircle(this.circleId, { signal });

      if (generation !== this.generation) {
        return;
      }

      this.update({
        circle: response.data,
        lastUpdatedAt: new Date(),
      });
    } catch (caught) {
      if (generation !== this.generation) {
        return;
      }

      const failure = toApiFailure(caught);

      if (failure.kind === "cancelled") {
        return;
      }

      this.update({
        error: { failure, occurredAt: new Date() },
      });
    } finally {
      if (generation === this.generation) {
        this.controller = null;
        this.update({ isLoading: false, isRefreshing: false });
      }
    }
  }
}
