import { router, useLocalSearchParams } from "expo-router";
import { useEffect, type ReactElement } from "react";
import { AccessibilityInfo, ScrollView, StyleSheet, Text, View } from "react-native";

import { Badge } from "@/components/badge";
import { CircleListSkeleton } from "@/components/circle-list-skeleton";
import { ConnectionBanner } from "@/components/connection-banner";
import { ErrorState, OfflineState } from "@/components/common-states";
import { DetailSection, InfoRow } from "@/components/detail-section";
import { SelfReportedRating } from "@/components/self-reported-rating";
import { colors, spacing } from "@/components/theme";
import { describeFailure } from "@/circles/failure-presentation";
import {
  formatCostAmount,
  formatCostLabel,
  formatLastUpdated,
  formatLocation,
  formatScheduleDetail,
  formatUniversity,
} from "@/circles/formatting";
import {
  ACTIVITY_FREQUENCY_LABELS,
  CAMP_FREQUENCY_LABELS,
  CIRCLE_TYPE_LABELS,
  GENDER_BALANCE_LABELS,
  MEMBER_COUNT_BAND_LABELS,
  OFFICIAL_STATUS_LABELS,
  RATING_DEFINITIONS,
  RECRUITING_STATUS_LABELS,
  SELF_REPORTED_NOTICE,
} from "@/circles/labels";
import type { CircleDetail } from "@/circles/types";
import { useCircleDetail } from "@/circles/use-circle-detail";
import { useDelayedFlag } from "@/circles/use-delayed-flag";

const UNANSWERED = "未回答";

function goBackToList() {
  if (router.canGoBack()) {
    router.back();
  } else {
    router.replace("/");
  }
}

function DetailLoading() {
  // Same 300ms rule as the lists: no skeleton flash for fast responses.
  const visible = useDelayedFlag(true);

  useEffect(() => {
    if (!visible) {
      return undefined;
    }

    AccessibilityInfo.announceForAccessibility("読み込み中です");

    return () => {
      AccessibilityInfo.announceForAccessibility("読み込みが終わりました");
    };
  }, [visible]);

  return (
    <View style={styles.padded}>{visible ? <CircleListSkeleton /> : null}</View>
  );
}

function CircleDetailContent({ circle }: { circle: CircleDetail }) {
  const officialLabel = OFFICIAL_STATUS_LABELS[circle.officialStatus];
  const hasGenderBalance = circle.genderBalanceCode !== null;

  return (
    <>
      <View style={styles.hero}>
        <Text accessibilityRole="header" style={styles.name}>
          {circle.displayName}
        </Text>
        <Text style={styles.headline}>{circle.headline}</Text>
        <View style={styles.badges}>
          <Badge emphasized={circle.officialStatus === "official"} label={officialLabel} />
          <Badge label={CIRCLE_TYPE_LABELS[circle.circleType]} />
          <Badge label={circle.category.name} />
          <Badge label={RECRUITING_STATUS_LABELS[circle.recruitingStatus]} />
        </View>
      </View>

      <DetailSection title="サークル紹介">
        <Text style={styles.body}>{circle.summary}</Text>
        {circle.description ? (
          <Text style={styles.body}>{circle.description}</Text>
        ) : null}
      </DetailSection>

      <DetailSection title="基本情報">
        <InfoRow label="大学" values={circle.universities.map(formatUniversity)} />
        <InfoRow
          label="活動場所"
          values={circle.activityLocations.flatMap((location) =>
            location.publicNote
              ? [formatLocation(location), location.publicNote]
              : [formatLocation(location)],
          )}
        />
        <InfoRow
          label="活動日時"
          values={circle.activitySchedules.flatMap((schedule) =>
            schedule.note
              ? [formatScheduleDetail(schedule), schedule.note]
              : [formatScheduleDetail(schedule)],
          )}
        />
        <InfoRow
          emptyText={UNANSWERED}
          label="規模"
          values={
            circle.memberCountBand
              ? [MEMBER_COUNT_BAND_LABELS[circle.memberCountBand]]
              : []
          }
        />
        <InfoRow
          emptyText={UNANSWERED}
          label="活動頻度"
          values={
            circle.activityFrequencyCode
              ? [ACTIVITY_FREQUENCY_LABELS[circle.activityFrequencyCode]]
              : []
          }
        />
        <InfoRow
          emptyText={UNANSWERED}
          label="合宿"
          values={
            circle.campFrequencyCode
              ? [CAMP_FREQUENCY_LABELS[circle.campFrequencyCode]]
              : []
          }
        />
      </DetailSection>

      <DetailSection title="費用">
        {circle.costs.length > 0 ? (
          circle.costs.map((cost, index) => (
            <InfoRow
              key={`${index}-${cost.costType}-${cost.label}`}
              label={formatCostLabel(cost)}
              values={[
                formatCostAmount(cost),
                ...(cost.note ? [cost.note] : []),
              ]}
            />
          ))
        ) : (
          <Text style={styles.body}>費用情報は登録されていません。</Text>
        )}
      </DetailSection>

      <DetailSection caption={SELF_REPORTED_NOTICE} title="雰囲気・特徴">
        {RATING_DEFINITIONS.map((definition) => (
          <SelfReportedRating
            key={definition.key}
            highLabel={definition.highLabel}
            label={definition.label}
            lowLabel={definition.lowLabel}
            value={circle[definition.key]}
          />
        ))}
        <InfoRow
          emptyText={UNANSWERED}
          label={`男女比（${SELF_REPORTED_NOTICE}）`}
          values={
            hasGenderBalance && circle.genderBalanceCode
              ? [GENDER_BALANCE_LABELS[circle.genderBalanceCode]]
              : []
          }
        />
      </DetailSection>

      {circle.tags.length > 0 ? (
        <DetailSection title="タグ">
          <Text style={styles.body}>
            {circle.tags.map((tag) => `#${tag.name}`).join("  ")}
          </Text>
        </DetailSection>
      ) : null}
    </>
  );
}

export default function CircleDetailScreen() {
  const { circleId } = useLocalSearchParams<{
    circleId?: string | string[];
  }>();
  const resolvedCircleId = Array.isArray(circleId) ? circleId[0] : circleId;
  const detail = useCircleDetail(resolvedCircleId);

  let body: ReactElement;

  if (!resolvedCircleId) {
    body = (
      <ErrorState
        description="サークルIDを確認できませんでした。"
        onSecondaryAction={goBackToList}
        secondaryActionLabel="一覧へ戻る"
        title="表示できません"
      />
    );
  } else if (detail.circle) {
    // A failed re-fetch keeps the Circle on screen and says so inline.
    const failure = detail.error
      ? describeFailure(detail.error.failure, detail.error.occurredAt)
      : null;

    body = (
      <>
        {failure ? (
          <ConnectionBanner
            description={
              failure.kind === "offline"
                ? "最後に取得した内容を表示しています。"
                : failure.description
            }
            lastUpdatedLabel={
              detail.lastUpdatedAt ? formatLastUpdated(detail.lastUpdatedAt) : undefined
            }
            onRetry={failure.canRetry ? detail.retry : undefined}
            requestId={failure.requestId}
            title={failure.title}
          />
        ) : null}
        <CircleDetailContent circle={detail.circle} />
      </>
    );
  } else if (detail.error) {
    const failure = describeFailure(detail.error.failure, detail.error.occurredAt);
    const onRetry = failure.canRetry ? detail.retry : undefined;

    body =
      failure.kind === "offline" ? (
        <OfflineState
          description={failure.description}
          onRetry={onRetry}
          title={failure.title}
        />
      ) : (
        <ErrorState
          description={failure.description}
          onRetry={onRetry}
          onSecondaryAction={goBackToList}
          requestId={failure.requestId}
          secondaryActionLabel="一覧へ戻る"
          title={failure.title}
        />
      );
  } else {
    body = <DetailLoading />;
  }

  return (
    <ScrollView
      contentContainerStyle={styles.content}
      style={styles.screen}
    >
      {body}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: {
    backgroundColor: colors.background,
    flex: 1,
  },
  content: {
    flexGrow: 1,
    gap: spacing.md,
    padding: spacing.lg,
  },
  padded: {
    paddingVertical: spacing.lg,
  },
  hero: {
    gap: spacing.sm,
  },
  name: {
    color: colors.textPrimary,
    fontSize: 26,
    fontWeight: "700",
  },
  headline: {
    color: colors.accent,
    fontSize: 16,
    fontWeight: "600",
    lineHeight: 23,
  },
  badges: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  body: {
    color: colors.textPrimary,
    fontSize: 15,
    lineHeight: 23,
  },
});
