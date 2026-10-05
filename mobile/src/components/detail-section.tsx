import type { ReactNode } from "react";
import { StyleSheet, Text, View } from "react-native";

import { colors, spacing } from "./theme";

export interface DetailSectionProps {
  children: ReactNode;
  /** Shown under the heading, e.g. the self-report notice. */
  caption?: string;
  title: string;
}

export function DetailSection({ caption, children, title }: DetailSectionProps) {
  return (
    <View style={styles.section}>
      <Text accessibilityRole="header" style={styles.title}>
        {title}
      </Text>
      {caption ? <Text style={styles.caption}>{caption}</Text> : null}
      {children}
    </View>
  );
}

export interface InfoRowProps {
  label: string;
  /** One line per entry; an empty list renders the unanswered text. */
  values: readonly string[];
  emptyText?: string;
}

/** Label above value, so long values wrap instead of overflowing at 200% text size. */
export function InfoRow({ emptyText = "未設定", label, values }: InfoRowProps) {
  const displayValues = values.length > 0 ? values : [emptyText];

  return (
    <View
      accessible
      accessibilityLabel={`${label}、${displayValues.join("、")}`}
      style={styles.row}
    >
      <Text style={styles.rowLabel}>{label}</Text>
      {displayValues.map((value, index) => (
        <Text key={`${index}-${value}`} style={styles.rowValue}>
          {value}
        </Text>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  section: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 12,
    borderWidth: 1,
    gap: spacing.md,
    padding: spacing.lg,
  },
  title: {
    color: colors.textPrimary,
    fontSize: 18,
    fontWeight: "700",
  },
  caption: {
    color: colors.accent,
    fontSize: 13,
    fontWeight: "700",
  },
  row: {
    gap: spacing.xs,
  },
  rowLabel: {
    color: colors.textMuted,
    fontSize: 13,
    fontWeight: "700",
  },
  rowValue: {
    color: colors.textPrimary,
    fontSize: 15,
    lineHeight: 22,
  },
});
