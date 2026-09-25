import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";

export const ROOT_STACK_ROUTES = {
  circleDetail: "circles/[circleId]",
  tabs: "(tabs)",
} as const;

export default function RootLayout() {
  return (
    <>
      <Stack>
        <Stack.Screen
          name={ROOT_STACK_ROUTES.tabs}
          options={{ headerShown: false }}
        />
        <Stack.Screen
          name={ROOT_STACK_ROUTES.circleDetail}
          options={{ title: "サークル詳細" }}
        />
      </Stack>
      <StatusBar style="dark" />
    </>
  );
}
