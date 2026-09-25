import type {
  GetCircleResponse,
  ListCirclesQuery,
  ListCirclesResponse,
} from "../src/api/circles";
import type { ProblemDetails } from "../src/api/problem-details";

const requestId = "00000000-0000-0000-0000-000000000000";
const circleId = "00000000-0000-0000-0000-000000000001";

const queryFixture = {
  q: "軽音",
  officialStatus: ["official"],
  weekday: ["1", "irregular"],
  tagId: [circleId],
  sort: "newest",
  cursor: "opaque-cursor",
  limit: 20,
} satisfies ListCirclesQuery;

const listFixture = {
  data: [],
  page: {
    totalCount: 0,
    hasMore: false,
    nextCursor: null,
    limit: 20,
  },
  meta: { requestId },
} satisfies ListCirclesResponse;

const detailFixture = {
  data: {
    id: circleId,
    displayName: "Example Circle",
    headline: "Headline",
    summary: "Summary",
    officialStatus: "official",
    circleType: "circle",
    publishedAt: "2026-09-23T00:00:00Z",
    category: { id: circleId, name: "文化", slug: "culture" },
    universities: [],
    featuredTags: [],
    activitySchedules: [],
    activityLocations: [],
    description: "Description",
    recruitingStatus: "open",
    memberCountBand: null,
    campFrequencyCode: null,
    activityFrequencyCode: null,
    livelinessRating: null,
    drinkingFrequencyRating: null,
    attendanceFlexibilityRating: null,
    commitmentRating: null,
    careerOpportunityRating: null,
    genderBalanceCode: null,
    tags: [],
    costs: [],
  },
  meta: { requestId },
} satisfies GetCircleResponse;

const problemFixture = {
  type: "about:blank",
  title: "Not Found",
  status: 404,
  detail: "The Circle was not found.",
  instance: `/api/v1/circles/${circleId}`,
  code: "NOT_FOUND",
  requestId,
  errors: null,
} satisfies ProblemDetails;

describe("generated OpenAPI type fixtures", () => {
  it("keeps Circle query, response, pagination, and Problem shapes typed", () => {
    expect(queryFixture.sort).toBe("newest");
    expect(listFixture.page.totalCount).toBe(0);
    expect(detailFixture.data.id).toBe(circleId);
    expect(problemFixture.code).toBe("NOT_FOUND");
  });
});
