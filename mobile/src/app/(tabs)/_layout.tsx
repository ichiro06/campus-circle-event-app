import { Tabs } from "expo-router";

export const TAB_ROUTES = [
  { name: "index", title: "ホーム" },
  { name: "search", title: "検索" },
  { name: "favorites", title: "お気に入り" },
  { name: "me", title: "マイページ" },
] as const;

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        headerTitleAlign: "center",
        tabBarActiveTintColor: "#16775D",
      }}
    >
      <Tabs.Screen
        name={TAB_ROUTES[0].name}
        options={{ title: TAB_ROUTES[0].title }}
      />
      <Tabs.Screen
        name={TAB_ROUTES[1].name}
        options={{ title: TAB_ROUTES[1].title }}
      />
      <Tabs.Screen
        name={TAB_ROUTES[2].name}
        options={{ title: TAB_ROUTES[2].title }}
      />
      <Tabs.Screen
        name={TAB_ROUTES[3].name}
        options={{ title: TAB_ROUTES[3].title }}
      />
    </Tabs>
  );
}
