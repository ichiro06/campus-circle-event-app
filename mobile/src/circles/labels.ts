import type { components } from "@/api/generated/openapi";

type Schemas = components["schemas"];

export const OFFICIAL_STATUS_LABELS: Record<Schemas["OfficialStatus"], string> = {
  official: "公認",
  unofficial: "非公認",
  unknown: "公認区分は未確認",
};

export const CIRCLE_TYPE_LABELS: Record<Schemas["CircleType"], string> = {
  circle: "サークル",
  club: "部活",
  intercollegiate: "インカレ",
  student_organization: "学生団体",
};

export const RECRUITING_STATUS_LABELS: Record<Schemas["RecruitingStatus"], string> = {
  open: "募集中",
  seasonal: "時期により募集",
  closed: "募集停止中",
  unknown: "募集状況は未確認",
};

export const MEMBER_COUNT_BAND_LABELS: Record<Schemas["MemberCountBand"], string> = {
  "1_10": "1〜10人",
  "11_30": "11〜30人",
  "31_80": "31〜80人",
  "81_150": "81〜150人",
  "151_plus": "151人以上",
  not_disclosed: "非公開",
};

export const CAMP_FREQUENCY_LABELS: Record<Schemas["CampFrequencyCode"], string> = {
  none: "なし",
  once_year: "年1回",
  twice_year: "年2回",
  three_plus_year: "年3回以上",
  unknown: "不明",
};

export const ACTIVITY_FREQUENCY_LABELS: Record<Schemas["ActivityFrequencyCode"], string> = {
  less_monthly: "月1回未満",
  monthly: "月1回",
  two_three_monthly: "月2〜3回",
  weekly: "週1回",
  two_three_weekly: "週2〜3回",
  four_plus_weekly: "週4回以上",
  irregular: "不定期",
};

export const GENDER_BALANCE_LABELS: Record<Schemas["GenderBalanceCode"], string> = {
  women_majority: "女性が多い",
  balanced: "概ね均衡",
  men_majority: "男性が多い",
  mixed_or_other: "多様・その他",
  not_disclosed: "非公開",
};

export const COST_TYPE_LABELS: Record<Schemas["CostType"], string> = {
  admission: "入会費",
  annual: "年会費",
  monthly: "月会費",
  per_event: "参加ごとの費用",
  other: "その他の費用",
};

export const TIME_BAND_LABELS: Record<Schemas["TimeBand"], string> = {
  morning: "午前",
  daytime: "昼",
  evening: "夕方",
  night: "夜",
  all_day: "終日",
  irregular: "不定期",
};

export const WEEKDAY_LABELS: Record<Schemas["WeekdayValue"], string> = {
  "1": "月曜日",
  "2": "火曜日",
  "3": "水曜日",
  "4": "木曜日",
  "5": "金曜日",
  "6": "土曜日",
  "7": "日曜日",
  irregular: "不定期",
};

export interface RatingDefinition {
  key:
    | "drinkingFrequencyRating"
    | "livelinessRating"
    | "commitmentRating"
    | "attendanceFlexibilityRating"
    | "careerOpportunityRating";
  label: string;
  /** Scale anchors from docs/data-dictionary.md section 6 (value 1 and value 5). */
  lowLabel: string;
  highLabel: string;
}

export const RATING_DEFINITIONS: readonly RatingDefinition[] = [
  {
    key: "drinkingFrequencyRating",
    label: "飲み会の頻度",
    lowLabel: "なし",
    highLabel: "週1回以上",
  },
  {
    key: "livelinessRating",
    label: "賑やかさ",
    lowLabel: "落ち着いている",
    highLabel: "とても賑やか",
  },
  {
    key: "commitmentRating",
    label: "活動の本気度",
    lowLabel: "気軽な交流中心",
    highLabel: "大会・公演・成果を強く重視",
  },
  {
    key: "attendanceFlexibilityRating",
    label: "出席自由度",
    lowLabel: "原則参加",
    highLabel: "完全に自由",
  },
  {
    key: "careerOpportunityRating",
    label: "ガクチカにつながる度",
    lowLabel: "役割機会は少ない",
    highLabel: "継続的な企画・対外活動機会がある",
  },
];

export const SELF_REPORTED_NOTICE = "団体による自己申告";
