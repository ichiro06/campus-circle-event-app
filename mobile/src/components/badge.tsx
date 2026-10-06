import { StyleSheet, Text, View } from "react-native";

import { colors, spacing } from "./theme";

export interface BadgeProps {
  label: string;
  /** Emphasized badges also change border weight, so status never relies on color alone. */
  emphasized?: boolean;
}

export function Badge({ emphasized = false, label }: BadgeProps) {
  return (
    <View style={[styles.badge, emphasized && styles.emphasized]}>
      <Text style={[styles.label, emphasized && styles.emphasizedLabel]}>
        {label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    borderColor: colors.border,
    borderRadius: 6,
    borderWidth: 1,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
  },
  emphasized: {
    backgroundColor: colors.accentSoft,
    borderColor: colors.accent,
    borderWidth: 2,
  },
  label: {
    color: colors.textMuted,
    fontSize: 13,
    fontWeight: "600",
  },
  emphasizedLabel: {
    color: colors.accent,
  },
});
