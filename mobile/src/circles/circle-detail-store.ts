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

/** Lifecycle of an accepted read that retains existing Circle data. */
export interface CircleDetailUpdateEvent {
  operationId: number;
  phase: "start" | "success" | "failure" | "cancelled";
}

type UpdateListener = (event: CircleDetailUpdateEvent) => void;

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
  private readonly updateListeners = new Set<UpdateListener>();
  private pendingUpdateId: number | null = null;
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

  /** Events are delivered directly, independently of snapshot/render batching. */
  subscribeToUpdates = (listener: UpdateListener): (() => void) => {
    this.updateListeners.add(listener);
    return () => { this.updateListeners.delete(listener); };
  };

  private emitUpdate(operationId: number, phase: CircleDetailUpdateEvent["phase"]): void {
    for (const listener of this.updateListeners) {
      listener({ operationId, phase });
    }
  }

  getSnapshot = (): CircleDetailSnapshot => this.snapshot;

  /** Safe to call again after stop(): it refetches only if nothing was loaded yet. */
  start(): void {
    this.active = true;
    if (this.snapshot.lastUpdatedAt === null && this.snapshot.error === null) {
      void this.load();
    }
  }

  stop(): void {
    const cancelledUpdateId = this.pendingUpdateId;
    this.pendingUpdateId = null;
    this.active = false;
    this.generation += 1;
    this.controller?.abort();
    this.controller = null;
    this.update({ isLoading: false, isRefreshing: false });
    if (cancelledUpdateId !== null) this.emitUpdate(cancelledUpdateId, "cancelled");
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

    // Initial reads belong to the Skeleton notification system. Only accepted
    // reads with retained data produce this operation lifecycle.
    const operationId = this.snapshot.circle ? generation : null;
    this.pendingUpdateId = operationId;
    this.update({ isLoading: true, isRefreshing, error: null });
    if (operationId !== null) this.emitUpdate(operationId, "start");
    let outcome: Exclude<CircleDetailUpdateEvent["phase"], "start"> = "cancelled";

    try {
      const response = await this.api.getCircle(this.circleId, { signal });

      if (generation !== this.generation) {
        return;
      }

      this.update({
        circle: response.data,
        lastUpdatedAt: new Date(),
      });
      outcome = "success";
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
      outcome = "failure";
    } finally {
      if (generation === this.generation) {
        this.controller = null;
        this.pendingUpdateId = null;
        this.update({ isLoading: false, isRefreshing: false });
        if (operationId !== null) this.emitUpdate(operationId, outcome);
      }
    }
  }
}
