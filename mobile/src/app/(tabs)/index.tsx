import { router } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import { CircleListView } from "@/components/circle-list";
import { EmptyState } from "@/components/common-states";
import { colors, spacing } from "@/components/theme";
import { useHomeCircles } from "@/circles/use-home-circles";

export default function HomeScreen() {
  const circles = useHomeCircles();

  return (
    <CircleListView
      circles={circles}
      emptyState={
        <EmptyState
          actionLabel="再読み込み"
          description="公開中のサークルがまだありません。時間をおいて再読み込みしてください。"
          onAction={circles.refresh}
          title="表示できるサークルがありません"
        />
      }
      header={
        <View style={styles.header}>
          <Text accessibilityRole="header" style={styles.title}>
            サークルを見つけよう
          </Text>
          <Text style={styles.description}>人気順の公開サークルです。</Text>
        </View>
      }
      onOpenCircle={(circleId) =>
        router.push({ pathname: "/circles/[circleId]", params: { circleId } })
      }
    />
  );
}

const styles = StyleSheet.create({
  header: {
    gap: spacing.xs,
  },
  title: {
    color: colors.textPrimary,
    fontSize: 28,
    fontWeight: "700",
  },
  description: {
    color: colors.textMuted,
    fontSize: 15,
    lineHeight: 22,
  },
});
