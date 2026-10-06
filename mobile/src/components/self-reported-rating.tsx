import { StyleSheet, Text, View } from "react-native";

import { colors, spacing } from "./theme";

export interface SelfReportedRatingProps {
  label: string;
  lowLabel: string;
  highLabel: string;
  /** 1 to 5, or null when the group has not answered. */
  value: number | null;
}

const SCALE_STEPS = [1, 2, 3, 4, 5] as const;

export function SelfReportedRating({
  highLabel,
  label,
  lowLabel,
  value,
}: SelfReportedRatingProps) {
  const valueText = value === null ? "未回答" : `5段階中 ${value}`;

  return (
    <View
      accessible
      accessibilityLabel={`${label}、${valueText}。1は${lowLabel}、5は${highLabel}`}
      style={styles.container}
    >
      <Text style={styles.label}>{label}</Text>
      <View style={styles.valueRow}>
        <View style={styles.scale}>
          {SCALE_STEPS.map((step) => (
            <View
              key={step}
              style={[
                styles.step,
                value !== null && step <= value && styles.stepFilled,
              ]}
            />
          ))}
        </View>
        <Text style={styles.value}>
          {value === null ? "未回答" : `${value} / 5`}
        </Text>
      </View>
      <Text style={styles.anchors}>
        1: {lowLabel} ／ 5: {highLabel}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: spacing.xs,
  },
  label: {
    color: colors.textPrimary,
    fontSize: 15,
    fontWeight: "700",
  },
  valueRow: {
    alignItems: "center",
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.md,
  },
  scale: {
    flexDirection: "row",
    gap: spacing.xs,
  },
  step: {
    backgroundColor: colors.surface,
    borderColor: colors.accent,
    borderRadius: 4,
    borderWidth: 2,
    height: 14,
    width: 28,
  },
  stepFilled: {
    backgroundColor: colors.accent,
  },
  value: {
    color: colors.textPrimary,
    fontSize: 15,
    fontWeight: "700",
  },
  anchors: {
    color: colors.textMuted,
    fontSize: 13,
    lineHeight: 19,
  },
});
