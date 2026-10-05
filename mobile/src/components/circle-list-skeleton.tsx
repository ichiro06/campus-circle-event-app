import { StyleSheet, View } from "react-native";

import { colors, spacing } from "./theme";

const SKELETON_CARD_COUNT = 3;

/** Placeholder with the same silhouette as CircleCard, shown after the 300ms delay. */
export function CircleListSkeleton() {
  return (
    <View
      accessible
      accessibilityLabel="読み込み中です"
      accessibilityRole="progressbar"
      style={styles.container}
    >
      {Array.from({ length: SKELETON_CARD_COUNT }, (_, index) => (
        <View key={index} style={styles.card}>
          <View style={styles.titleRow}>
            <View style={styles.avatar} />
            <View style={styles.titleText}>
              <View style={[styles.line, styles.lineWide]} />
              <View style={[styles.line, styles.lineMedium]} />
            </View>
          </View>
          <View style={[styles.line, styles.lineFull]} />
          <View style={[styles.line, styles.lineMedium]} />
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: spacing.md,
  },
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 12,
    borderWidth: 1,
    gap: spacing.md,
    padding: spacing.lg,
  },
  titleRow: {
    flexDirection: "row",
    gap: spacing.md,
  },
  avatar: {
    backgroundColor: colors.border,
    borderRadius: 10,
    height: 48,
    width: 48,
  },
  titleText: {
    flex: 1,
    gap: spacing.sm,
    justifyContent: "center",
  },
  line: {
    backgroundColor: colors.border,
    borderRadius: 4,
    height: 14,
  },
  lineWide: {
    width: "70%",
  },
  lineMedium: {
    width: "50%",
  },
  lineFull: {
    width: "100%",
  },
});
