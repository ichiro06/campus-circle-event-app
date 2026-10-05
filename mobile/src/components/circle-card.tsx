import { memo } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import {
  formatLocation,
  formatScheduleSummary,
  formatUniversity,
} from "@/circles/formatting";
import { CIRCLE_TYPE_LABELS, OFFICIAL_STATUS_LABELS } from "@/circles/labels";
import type { CircleListItem } from "@/circles/types";

import { Badge } from "./badge";
import { colors, MIN_TAP_TARGET, spacing } from "./theme";

export interface CircleCardProps {
  circle: CircleListItem;
  onPress: (circleId: string) => void;
}

function buildCardFacts(circle: CircleListItem): string[] {
  return [
    ...circle.universities.map(formatUniversity),
    ...circle.activityLocations.map(formatLocation),
    ...circle.activitySchedules.map(formatScheduleSummary),
  ];
}

function CircleCardView({ circle, onPress }: CircleCardProps) {
  const facts = buildCardFacts(circle);
  const officialLabel = OFFICIAL_STATUS_LABELS[circle.officialStatus];
  const typeLabel = CIRCLE_TYPE_LABELS[circle.circleType];
  const tagLabels = circle.featuredTags.map((tag) => `#${tag.name}`);

  // The card is one control, so the label carries everything a screen reader needs.
  const accessibilityLabel = [
    circle.displayName,
    circle.headline,
    `${officialLabel}、${typeLabel}`,
    ...facts,
    tagLabels.length > 0 ? `タグ ${tagLabels.join("、")}` : null,
  ]
    .filter(Boolean)
    .join("。");

  return (
    <Pressable
      accessibilityHint="サークルの詳細を開きます"
      accessibilityLabel={accessibilityLabel}
      accessibilityRole="button"
      onPress={() => onPress(circle.id)}
      style={({ pressed }) => [styles.card, pressed && styles.pressed]}
    >
      <View style={styles.titleRow}>
        {/* The API returns no image, so a decorative initial stands in for one. */}
        <View
          accessibilityElementsHidden
          importantForAccessibility="no-hide-descendants"
          style={styles.placeholder}
        >
          <Text style={styles.placeholderText}>
            {Array.from(circle.displayName)[0] ?? "?"}
          </Text>
        </View>
        <View style={styles.titleText}>
          <Text style={styles.name}>{circle.displayName}</Text>
          <Text style={styles.headline}>{circle.headline}</Text>
        </View>
      </View>
      <Text style={styles.summary}>{circle.summary}</Text>
      <View style={styles.badges}>
        <Badge
          emphasized={circle.officialStatus === "official"}
          label={officialLabel}
        />
        <Badge label={typeLabel} />
      </View>
      {facts.map((fact, index) => (
        <Text key={`${index}-${fact}`} style={styles.fact}>
          {fact}
        </Text>
      ))}
      {tagLabels.length > 0 ? (
        <Text style={styles.tags}>{tagLabels.join("  ")}</Text>
      ) : null}
    </Pressable>
  );
}

export const CircleCard = memo(CircleCardView);

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 12,
    borderWidth: 1,
    gap: spacing.sm,
    minHeight: MIN_TAP_TARGET,
    padding: spacing.lg,
  },
  pressed: {
    opacity: 0.7,
  },
  titleRow: {
    alignItems: "flex-start",
    flexDirection: "row",
    gap: spacing.md,
  },
  placeholder: {
    alignItems: "center",
    backgroundColor: colors.accentSoft,
    borderRadius: 10,
    height: MIN_TAP_TARGET,
    justifyContent: "center",
    width: MIN_TAP_TARGET,
  },
  placeholderText: {
    color: colors.accent,
    fontSize: 20,
    fontWeight: "700",
  },
  titleText: {
    flex: 1,
    flexShrink: 1,
    gap: spacing.xs,
  },
  name: {
    color: colors.textPrimary,
    fontSize: 18,
    fontWeight: "700",
  },
  headline: {
    color: colors.accent,
    fontSize: 15,
    fontWeight: "600",
  },
  summary: {
    color: colors.textMuted,
    fontSize: 14,
    lineHeight: 21,
  },
  badges: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  fact: {
    color: colors.textMuted,
    fontSize: 13,
    lineHeight: 19,
  },
  tags: {
    color: colors.accent,
    fontSize: 13,
    lineHeight: 19,
  },
});
