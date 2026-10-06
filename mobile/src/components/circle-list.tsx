import { useEffect, type ReactElement } from "react";
import {
  AccessibilityInfo,
  ActivityIndicator,
  FlatList,
  RefreshControl,
  StyleSheet,
  View,
} from "react-native";

import { describeFailure } from "@/circles/failure-presentation";
import { formatLastUpdated } from "@/circles/formatting";
import type { CircleListItem } from "@/circles/types";
import { useDelayedFlag } from "@/circles/use-delayed-flag";
import type {
  CircleListError,
  PaginatedCircles,
} from "@/circles/use-paginated-circles";

import { CircleCard } from "./circle-card";
import { CircleListSkeleton } from "./circle-list-skeleton";
import { ConnectionBanner } from "./connection-banner";
import { ErrorState, OfflineState } from "./common-states";
import { colors, spacing } from "./theme";

export interface CircleListViewProps {
  circles: PaginatedCircles;
  /** Content above the cards, such as the screen title or the search controls. */
  header?: ReactElement;
  /** Shown when the request succeeded but nothing matched. */
  emptyState: ReactElement;
  onOpenCircle: (circleId: string) => void;
}

function keyExtractor(circle: CircleListItem): string {
  return circle.id;
}

function InitialLoading() {
  // Nothing is drawn for the first 300ms so fast responses do not flash a skeleton.
  const visible = useDelayedFlag(true);

  useEffect(() => {
    if (!visible) {
      return undefined;
    }

    AccessibilityInfo.announceForAccessibility("読み込み中です");

    return () => {
      AccessibilityInfo.announceForAccessibility("読み込みが終わりました");
    };
  }, [visible]);

  return visible ? <CircleListSkeleton /> : null;
}

function FullScreenError({
  circles,
  error,
}: {
  circles: PaginatedCircles;
  error: CircleListError;
}) {
  const presentation = describeFailure(error.failure, error.occurredAt);
  const onRetry = presentation.canRetry ? circles.retry : undefined;

  if (presentation.kind === "offline") {
    return (
      <OfflineState
        description={presentation.description}
        onRetry={onRetry}
        title={presentation.title}
      />
    );
  }

  return (
    <ErrorState
      description={presentation.description}
      onRetry={onRetry}
      requestId={presentation.requestId}
      title={presentation.title}
    />
  );
}

function ErrorBanner({
  circles,
  error,
}: {
  circles: PaginatedCircles;
  error: CircleListError;
}) {
  const presentation = describeFailure(error.failure, error.occurredAt);

  return (
    <ConnectionBanner
      description={
        presentation.kind === "offline"
          ? "最後に取得した内容を表示しています。"
          : presentation.description
      }
      lastUpdatedLabel={
        circles.lastUpdatedAt ? formatLastUpdated(circles.lastUpdatedAt) : undefined
      }
      onRetry={presentation.canRetry ? circles.retry : undefined}
      requestId={presentation.requestId}
      title={presentation.title}
    />
  );
}

export function CircleListView({
  circles,
  emptyState,
  header,
  onOpenCircle,
}: CircleListViewProps) {
  const { error, items } = circles;

  let empty: ReactElement | null;

  if (circles.isInitialLoading) {
    empty = <InitialLoading />;
  } else if (error) {
    empty = <FullScreenError circles={circles} error={error} />;
  } else {
    empty = emptyState;
  }

  const showTopBanner = items.length > 0 && error && error.phase !== "more";
  const showMoreError = items.length > 0 && error?.phase === "more";

  return (
    <FlatList
      contentContainerStyle={styles.content}
      data={items}
      ItemSeparatorComponent={Separator}
      keyboardShouldPersistTaps="handled"
      keyExtractor={keyExtractor}
      ListEmptyComponent={empty}
      ListFooterComponent={
        circles.isLoadingMore ? (
          <ActivityIndicator
            accessibilityLabel="続きを読み込み中です"
            color={colors.accent}
            style={styles.footer}
          />
        ) : showMoreError && error ? (
          <View style={styles.footer}>
            <ErrorBanner circles={circles} error={error} />
          </View>
        ) : null
      }
      ListHeaderComponent={
        <View style={styles.header}>
          {header}
          {showTopBanner && error ? (
            <ErrorBanner circles={circles} error={error} />
          ) : null}
        </View>
      }
      onEndReached={circles.loadMore}
      onEndReachedThreshold={0.5}
      refreshControl={
        <RefreshControl
          colors={[colors.accent]}
          onRefresh={circles.refresh}
          refreshing={circles.isRefreshing}
          tintColor={colors.accent}
        />
      }
      renderItem={({ item }) => (
        <CircleCard circle={item} onPress={onOpenCircle} />
      )}
      style={styles.list}
      testID="circle-list"
    />
  );
}

function Separator() {
  return <View style={styles.separator} />;
}

const styles = StyleSheet.create({
  list: {
    backgroundColor: colors.background,
    flex: 1,
  },
  content: {
    flexGrow: 1,
    padding: spacing.lg,
  },
  header: {
    gap: spacing.md,
    marginBottom: spacing.md,
  },
  separator: {
    height: spacing.md,
  },
  footer: {
    marginTop: spacing.lg,
  },
});
