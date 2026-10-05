import { Pressable, StyleSheet, Text, View } from "react-native";

import { colors, MIN_TAP_TARGET, spacing } from "./theme";

export interface ConnectionBannerProps {
  description: string;
  /** Always shown with the data kept on screen, e.g. "最終更新 12:30". */
  lastUpdatedLabel?: string;
  onRetry?: () => void;
  requestId?: string;
  title: string;
}

/** Inline notice used when a refresh or next page failed but earlier data is still shown. */
export function ConnectionBanner({
  description,
  lastUpdatedLabel,
  onRetry,
  requestId,
  title,
}: ConnectionBannerProps) {
  return (
    <View style={styles.banner}>
      <View
        accessible
        accessibilityLabel={[title, description, lastUpdatedLabel]
          .filter(Boolean)
          .join("。")}
        accessibilityRole="alert"
        style={styles.text}
      >
        <Text style={styles.title}>{title}</Text>
        <Text style={styles.description}>{description}</Text>
        {lastUpdatedLabel ? (
          <Text style={styles.meta}>{lastUpdatedLabel}</Text>
        ) : null}
        {requestId ? (
          <Text selectable style={styles.meta}>
            問い合わせID: {requestId}
          </Text>
        ) : null}
      </View>
      {onRetry ? (
        <Pressable
          accessibilityRole="button"
          onPress={onRetry}
          style={styles.action}
        >
          <Text style={styles.actionLabel}>再試行</Text>
        </Pressable>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  banner: {
    backgroundColor: colors.surface,
    borderColor: colors.danger,
    borderRadius: 10,
    borderWidth: 2,
    gap: spacing.md,
    padding: spacing.lg,
  },
  text: {
    gap: spacing.xs,
  },
  title: {
    color: colors.danger,
    fontSize: 16,
    fontWeight: "700",
  },
  description: {
    color: colors.textPrimary,
    fontSize: 14,
    lineHeight: 21,
  },
  meta: {
    color: colors.textMuted,
    fontSize: 13,
  },
  action: {
    alignSelf: "flex-start",
    backgroundColor: colors.accent,
    borderRadius: 8,
    justifyContent: "center",
    minHeight: MIN_TAP_TARGET,
    paddingHorizontal: spacing.xl,
  },
  actionLabel: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "700",
  },
});
