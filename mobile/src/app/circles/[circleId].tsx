import { useLocalSearchParams } from "expo-router";

import { ShellScreen } from "@/components/shell-screen";

export default function CircleDetailScreen() {
  const { circleId } = useLocalSearchParams<{
    circleId?: string | string[];
  }>();
  const resolvedCircleId = Array.isArray(circleId) ? circleId[0] : circleId;

  return (
    <ShellScreen
      description={
        resolvedCircleId
          ? `サークルID: ${resolvedCircleId}`
          : "サークルIDを確認できませんでした。"
      }
      title="サークル詳細"
    />
  );
}
