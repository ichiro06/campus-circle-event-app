import { router } from "expo-router";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { CircleListView } from "@/components/circle-list";
import { ChoiceChip } from "@/components/choice-chip";
import { EmptyState } from "@/components/common-states";
import { colors, MIN_TAP_TARGET, spacing } from "@/components/theme";
import { CIRCLE_TYPE_LABELS, OFFICIAL_STATUS_LABELS } from "@/circles/labels";
import {
  mergeTagChoices,
  selectedTagIds,
  toggleTag,
} from "@/circles/tag-selection";
import type {
  CircleListFilters,
  CircleSort,
  CircleType,
  OfficialStatus,
  PublicTag,
} from "@/circles/types";
import { usePaginatedCircles } from "@/circles/use-paginated-circles";
import { usePublicTags } from "@/circles/use-public-tags";

export const SEARCH_DEBOUNCE_MS = 500;

const SORT_OPTIONS: readonly { label: string; value: CircleSort }[] = [
  { label: "新着順", value: "newest" },
  { label: "お気に入り数順", value: "most_favorited" },
];

// "unknown" exists in the API but is not a choice in docs/requirements.md (公認 / 非公認).
const OFFICIAL_STATUS_OPTIONS: readonly OfficialStatus[] = [
  "official",
  "unofficial",
];

const CIRCLE_TYPE_OPTIONS: readonly CircleType[] = [
  "circle",
  "club",
  "intercollegiate",
  "student_organization",
];

function toggle<Value>(values: readonly Value[], value: Value): Value[] {
  return values.includes(value)
    ? values.filter((current) => current !== value)
    : [...values, value];
}

/** Keeps selections in option order so equal choices always produce the same query. */
function inOrder<Value>(
  options: readonly Value[],
  selected: readonly Value[],
): Value[] {
  return options.filter((option) => selected.includes(option));
}

export default function SearchScreen() {
  const [draftKeyword, setDraftKeyword] = useState("");
  const [keyword, setKeyword] = useState("");
  const [sort, setSort] = useState<CircleSort>("newest");
  const [officialStatuses, setOfficialStatuses] = useState<OfficialStatus[]>([]);
  const [circleTypes, setCircleTypes] = useState<CircleType[]>([]);
  // Whole tags rather than IDs: a selected tag that later leaves the catalog keeps its label.
  const [selectedTags, setSelectedTags] = useState<PublicTag[]>([]);
  const publicTags = usePublicTags();
  const tagChoices = useMemo(
    () => mergeTagChoices(publicTags.tags, selectedTags),
    [publicTags.tags, selectedTags],
  );

  // A whitespace-only keyword normalizes to "", i.e. the query that is already active, so it
  // neither adds a q parameter nor triggers a request.
  const commitKeyword = useCallback((value: string) => {
    setKeyword(value.trim());
  }, []);

  useEffect(() => {
    const timeoutId = setTimeout(
      () => commitKeyword(draftKeyword),
      SEARCH_DEBOUNCE_MS,
    );

    return () => clearTimeout(timeoutId);
  }, [commitKeyword, draftKeyword]);

  const filters = useMemo<CircleListFilters>(() => {
    const next: CircleListFilters = { sort };

    if (keyword) {
      next.q = keyword;
    }

    if (officialStatuses.length > 0) {
      next.officialStatus = inOrder(OFFICIAL_STATUS_OPTIONS, officialStatuses);
    }

    if (circleTypes.length > 0) {
      next.circleType = inOrder(CIRCLE_TYPE_OPTIONS, circleTypes);
    }

    const tagIds = selectedTagIds(tagChoices, selectedTags);

    if (tagIds.length > 0) {
      next.tagId = tagIds;
    }

    return next;
  }, [circleTypes, keyword, officialStatuses, selectedTags, sort, tagChoices]);

  const circles = usePaginatedCircles(filters);
  const hasConditions =
    keyword !== "" ||
    officialStatuses.length > 0 ||
    circleTypes.length > 0 ||
    selectedTags.length > 0;

  const { refresh: refreshTags } = publicTags;
  const { refresh: refreshCircles } = circles;
  // Pulling to refresh also reloads the tag choices. A failure there never reaches the list.
  const listWithTagRefresh = {
    ...circles,
    refresh: () => {
      refreshCircles();
      refreshTags();
    },
  };

  const clearConditions = useCallback(() => {
    setDraftKeyword("");
    setKeyword("");
    setOfficialStatuses([]);
    setCircleTypes([]);
    setSelectedTags([]);
  }, []);

  return (
    <CircleListView
      circles={listWithTagRefresh}
      emptyState={
        hasConditions ? (
          <EmptyState
            actionLabel="検索条件を解除"
            description="キーワードや絞り込み条件を減らして、もう一度お試しください。"
            onAction={clearConditions}
            title="条件に合うサークルが見つかりません"
          />
        ) : (
          <EmptyState
            actionLabel="再読み込み"
            description="公開中のサークルがまだありません。時間をおいて再読み込みしてください。"
            onAction={circles.refresh}
            title="表示できるサークルがありません"
          />
        )
      }
      header={
        <View style={styles.header}>
          <Text accessibilityRole="header" style={styles.title}>
            サークルを検索
          </Text>
          <View style={styles.searchRow}>
            <TextInput
              accessibilityLabel="キーワード検索"
              autoCapitalize="none"
              autoCorrect={false}
              onChangeText={setDraftKeyword}
              onSubmitEditing={() => commitKeyword(draftKeyword)}
              placeholder="サークル名・活動内容・大学名など"
              placeholderTextColor={colors.textSubtle}
              returnKeyType="search"
              style={styles.input}
              value={draftKeyword}
            />
            {draftKeyword !== "" ? (
              <Pressable
                accessibilityLabel="入力を消去"
                accessibilityRole="button"
                onPress={() => {
                  setDraftKeyword("");
                  setKeyword("");
                }}
                style={styles.clear}
              >
                <Text style={styles.clearLabel}>消去</Text>
              </Pressable>
            ) : null}
          </View>

          <Text style={styles.groupLabel}>並び替え</Text>
          <View accessibilityRole="radiogroup" style={styles.chips}>
            {SORT_OPTIONS.map((option) => (
              <ChoiceChip
                key={option.value}
                label={option.label}
                onPress={() => setSort(option.value)}
                role="radio"
                selected={sort === option.value}
              />
            ))}
          </View>

          <Text style={styles.groupLabel}>公認区分</Text>
          <View style={styles.chips}>
            {OFFICIAL_STATUS_OPTIONS.map((option) => (
              <ChoiceChip
                key={option}
                label={OFFICIAL_STATUS_LABELS[option]}
                onPress={() =>
                  setOfficialStatuses((current) => toggle(current, option))
                }
                role="checkbox"
                selected={officialStatuses.includes(option)}
              />
            ))}
          </View>

          <Text style={styles.groupLabel}>団体種別</Text>
          <View style={styles.chips}>
            {CIRCLE_TYPE_OPTIONS.map((option) => (
              <ChoiceChip
                key={option}
                label={CIRCLE_TYPE_LABELS[option]}
                onPress={() => setCircleTypes((current) => toggle(current, option))}
                role="checkbox"
                selected={circleTypes.includes(option)}
              />
            ))}
          </View>

          {tagChoices.length > 0 ? (
            <>
              <Text style={styles.groupLabel}>タグ</Text>
              <Text style={styles.hint}>
                選んだタグのいずれかに該当するサークルを表示します（複数選択可）
              </Text>
              <View style={styles.chips}>
                {tagChoices.map((tag) => (
                  <ChoiceChip
                    key={tag.id}
                    label={tag.name}
                    onPress={() =>
                      setSelectedTags((current) => toggleTag(current, tag))
                    }
                    role="checkbox"
                    selected={selectedTags.some((current) => current.id === tag.id)}
                  />
                ))}
              </View>
            </>
          ) : null}

          {publicTags.status === "error" && publicTags.tags.length === 0 ? (
            <View style={styles.tagError}>
              <Text style={styles.hint}>タグを読み込めませんでした</Text>
              <Pressable
                accessibilityLabel="タグの読み込みを再試行"
                accessibilityRole="button"
                onPress={publicTags.refresh}
                style={styles.clear}
              >
                <Text style={styles.clearLabel}>再試行</Text>
              </Pressable>
            </View>
          ) : null}

          {circles.totalCount !== null ? (
            <Text accessibilityLiveRegion="polite" style={styles.count}>
              該当 {circles.totalCount} 件
            </Text>
          ) : null}
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
    gap: spacing.sm,
  },
  title: {
    color: colors.textPrimary,
    fontSize: 28,
    fontWeight: "700",
  },
  searchRow: {
    alignItems: "center",
    flexDirection: "row",
    gap: spacing.sm,
  },
  input: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 10,
    borderWidth: 1,
    color: colors.textPrimary,
    flex: 1,
    fontSize: 16,
    minHeight: MIN_TAP_TARGET,
    paddingHorizontal: spacing.md,
  },
  clear: {
    justifyContent: "center",
    minHeight: MIN_TAP_TARGET,
    minWidth: MIN_TAP_TARGET,
    paddingHorizontal: spacing.sm,
  },
  clearLabel: {
    color: colors.accent,
    fontSize: 15,
    fontWeight: "700",
  },
  groupLabel: {
    color: colors.textMuted,
    fontSize: 13,
    fontWeight: "700",
    marginTop: spacing.sm,
  },
  hint: {
    color: colors.textMuted,
    fontSize: 13,
  },
  tagError: {
    alignItems: "center",
    flexDirection: "row",
    gap: spacing.sm,
    marginTop: spacing.sm,
  },
  chips: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  count: {
    color: colors.textPrimary,
    fontSize: 15,
    fontWeight: "700",
    marginTop: spacing.sm,
  },
});
