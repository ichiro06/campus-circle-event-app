import { Pressable, StyleSheet, Text } from "react-native";

import { colors, MIN_TAP_TARGET, spacing } from "./theme";

export interface ChoiceChipProps {
  label: string;
  onPress: () => void;
  selected: boolean;
  /** "radio" for exclusive choices such as sort, "checkbox" for multi-select filters. */
  role: "checkbox" | "radio";
}

export function ChoiceChip({ label, onPress, role, selected }: ChoiceChipProps) {
  return (
    <Pressable
      accessibilityLabel={label}
      accessibilityRole={role}
      accessibilityState={role === "radio" ? { selected } : { checked: selected }}
      onPress={onPress}
      style={[styles.chip, selected && styles.selected]}
    >
      <Text style={[styles.label, selected && styles.selectedLabel]}>
        {selected ? "✓ " : ""}
        {label}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  chip: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: MIN_TAP_TARGET / 2,
    borderWidth: 1,
    justifyContent: "center",
    minHeight: MIN_TAP_TARGET,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
  },
  selected: {
    backgroundColor: colors.accentSoft,
    borderColor: colors.accent,
    borderWidth: 2,
  },
  label: {
    color: colors.textPrimary,
    fontSize: 15,
  },
  selectedLabel: {
    color: colors.accent,
    fontWeight: "700",
  },
});
