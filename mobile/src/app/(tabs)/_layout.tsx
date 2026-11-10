import { Tabs } from "expo-router";
import { SymbolView, type SymbolViewProps } from "expo-symbols";
import type { ColorValue } from "react-native";

export const TAB_ROUTES = [
  { name: "index", title: "ホーム" },
  { name: "search", title: "検索" },
  { name: "favorites", title: "お気に入り" },
  { name: "me", title: "マイページ" },
] as const;

type TabRouteName = (typeof TAB_ROUTES)[number]["name"];

/**
 * Tab icons from each platform's own symbol set: SF Symbols on iOS (Apple HIG)
 * and Material Symbols on Android (Material Design 3). DEC-070.
 *
 * Unselected tabs use the outline icon. On iOS the selected tab switches to the
 * filled variant where SF Symbols has one; `magnifyingglass` has none. The
 * Material Symbols font that expo-symbols bundles is outline-only, so Android
 * keeps the outline icon when selected.
 */
export const TAB_ICONS = {
  index: {
    default: { ios: "house", android: "home", web: "home" },
    selected: { ios: "house.fill", android: "home", web: "home" },
  },
  search: {
    default: { ios: "magnifyingglass", android: "search", web: "search" },
    selected: { ios: "magnifyingglass", android: "search", web: "search" },
  },
  favorites: {
    default: { ios: "heart", android: "favorite", web: "favorite" },
    selected: { ios: "heart.fill", android: "favorite", web: "favorite" },
  },
  me: {
    default: { ios: "person", android: "person", web: "person" },
    selected: { ios: "person.fill", android: "person", web: "person" },
  },
} as const satisfies Record<
  TabRouteName,
  Record<"default" | "selected", SymbolViewProps["name"]>
>;

function createTabIcon(routeName: TabRouteName) {
  // The tab label already names the destination, so the icon stays decorative
  // and the screen reader announces the tab only once.
  function TabIcon({
    color,
    focused,
    size,
  }: {
    color: ColorValue;
    focused: boolean;
    size: number;
  }) {
    return (
      <SymbolView
        accessibilityElementsHidden
        importantForAccessibility="no-hide-descendants"
        name={TAB_ICONS[routeName][focused ? "selected" : "default"]}
        size={size}
        tintColor={color}
      />
    );
  }
  return TabIcon;
}

// Created once so the tab bar does not remount the icons on every render.
const TAB_BAR_ICONS = {
  index: createTabIcon("index"),
  search: createTabIcon("search"),
  favorites: createTabIcon("favorites"),
  me: createTabIcon("me"),
} satisfies Record<TabRouteName, ReturnType<typeof createTabIcon>>;

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
        options={{
          tabBarIcon: TAB_BAR_ICONS[TAB_ROUTES[0].name],
          title: TAB_ROUTES[0].title,
        }}
      />
      <Tabs.Screen
        name={TAB_ROUTES[1].name}
        options={{
          tabBarIcon: TAB_BAR_ICONS[TAB_ROUTES[1].name],
          title: TAB_ROUTES[1].title,
        }}
      />
      <Tabs.Screen
        name={TAB_ROUTES[2].name}
        options={{
          tabBarIcon: TAB_BAR_ICONS[TAB_ROUTES[2].name],
          title: TAB_ROUTES[2].title,
        }}
      />
      <Tabs.Screen
        name={TAB_ROUTES[3].name}
        options={{
          tabBarIcon: TAB_BAR_ICONS[TAB_ROUTES[3].name],
          title: TAB_ROUTES[3].title,
        }}
      />
    </Tabs>
  );
}
