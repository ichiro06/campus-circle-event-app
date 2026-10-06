import {
  ApiClientError,
  type CirclesApi,
  type GetCircleResponse,
  type ListCirclesResponse,
} from "../src/api";
import type { CircleDetail, CircleListItem } from "../src/circles/types";

export const REQUEST_ID = "00000000-0000-0000-0000-0000000000aa";

export function circleId(index: number): string {
  return `10000000-0000-0000-0000-${String(index).padStart(12, "0")}`;
}

export function makeCircle(
  index: number,
  overrides: Partial<CircleListItem> = {},
): CircleListItem {
  return {
    id: circleId(index),
    displayName: `テストサークル${index}`,
    headline: `キャッチコピー${index}`,
    summary: `主な活動内容${index}`,
    officialStatus: "official",
    circleType: "circle",
    publishedAt: "2026-09-01T00:00:00Z",
    category: { id: circleId(900), name: "音楽", slug: "music" },
    universities: [
      {
        id: circleId(901),
        name: "法政大学",
        slug: "hosei",
        relationshipType: "primary",
        campus: "市ヶ谷",
      },
    ],
    featuredTags: [{ id: circleId(902), name: "初心者歓迎", slug: "beginner" }],
    activitySchedules: [
      {
        weekday: "1",
        timeBand: "evening",
        startsAt: "18:00:00",
        endsAt: "20:00:00",
        note: null,
      },
    ],
    activityLocations: [
      {
        prefecture: "東京都",
        city: "千代田区",
        facilityName: "学生会館",
        nearestStation: "市ヶ谷",
        isOnline: false,
        publicNote: null,
      },
    ],
    ...overrides,
  };
}

export function makeDetail(
  index: number,
  overrides: Partial<CircleDetail> = {},
): CircleDetail {
  return {
    ...makeCircle(index),
    description: `詳しい説明${index}`,
    recruitingStatus: "open",
    memberCountBand: "31_80",
    campFrequencyCode: "once_year",
    activityFrequencyCode: "weekly",
    drinkingFrequencyRating: 2,
    livelinessRating: 4,
    commitmentRating: null,
    attendanceFlexibilityRating: 3,
    careerOpportunityRating: 5,
    genderBalanceCode: "balanced",
    tags: [
      { id: circleId(902), name: "初心者歓迎", slug: "beginner", isFeatured: true },
      { id: circleId(903), name: "ライブ", slug: "live", isFeatured: false },
    ],
    costs: [
      {
        costType: "annual",
        amountMinYen: 3000,
        amountMaxYen: null,
        label: "年会費",
        note: "新入生は無料",
      },
    ],
    ...overrides,
  };
}

export interface ListPage {
  items: CircleListItem[];
  nextCursor?: string;
  totalCount?: number;
}

export function makeListResponse({
  items,
  nextCursor,
  totalCount = items.length,
}: ListPage): ListCirclesResponse {
  return {
    data: items,
    page: {
      hasMore: nextCursor !== undefined,
      limit: 20,
      nextCursor: nextCursor ?? null,
      totalCount,
    },
    meta: { requestId: REQUEST_ID },
  } as ListCirclesResponse;
}

export function makeDetailResponse(circle: CircleDetail): GetCircleResponse {
  return { data: circle, meta: { requestId: REQUEST_ID } } as GetCircleResponse;
}

export function problemFailure(
  status: number,
  code: string,
  extra: { retryAfterMs?: number } = {},
): ApiClientError {
  return new ApiClientError({
    kind: "problem",
    httpStatus: status,
    problem: {
      type: "about:blank",
      title: "internal title that must not be shown",
      status,
      detail: "internal detail SELECT * FROM secrets",
      instance: "/api/v1/circles",
      code,
      requestId: REQUEST_ID,
    } as never,
    ...extra,
  });
}

export function networkFailure(): ApiClientError {
  return new ApiClientError({ kind: "network" });
}

export function createMockApi(): {
  api: CirclesApi;
  getCircle: jest.Mock;
  listCircles: jest.Mock;
} {
  const getCircle = jest.fn();
  const listCircles = jest.fn();

  return { api: { getCircle, listCircles }, getCircle, listCircles };
}
