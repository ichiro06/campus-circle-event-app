import type { CircleDetail, CircleListItem } from "./types";
import { COST_TYPE_LABELS, TIME_BAND_LABELS, WEEKDAY_LABELS } from "./labels";

type ActivitySchedule = CircleListItem["activitySchedules"][number];
type ActivityLocation = CircleListItem["activityLocations"][number];
type University = CircleListItem["universities"][number];
type Cost = CircleDetail["costs"][number];

export function formatUniversity(university: University): string {
  return university.campus
    ? `${university.name} ${university.campus}`
    : university.name;
}

export function formatLocation(location: ActivityLocation): string {
  const parts = [
    location.isOnline ? "オンライン" : null,
    [location.prefecture, location.city].filter(Boolean).join("") || null,
    location.facilityName,
    location.nearestStation ? `最寄駅 ${location.nearestStation}` : null,
  ].filter((part): part is string => Boolean(part));

  return parts.length > 0 ? parts.join("・") : "場所は未設定";
}

function formatTime(value: string | null): string | null {
  return value ? value.slice(0, 5) : null;
}

/** Short form for cards: weekday and time band only. */
export function formatScheduleSummary(schedule: ActivitySchedule): string {
  if (schedule.weekday === "irregular" && schedule.timeBand === "irregular") {
    return "不定期";
  }

  return `${WEEKDAY_LABELS[schedule.weekday]} ${TIME_BAND_LABELS[schedule.timeBand]}`;
}

/** Detail form: adds the clock range when the API provides one. */
export function formatScheduleDetail(schedule: ActivitySchedule): string {
  const start = formatTime(schedule.startsAt);
  const end = formatTime(schedule.endsAt);
  const range = start && end ? `${start}〜${end}` : start ? `${start}〜` : null;
  const summary = formatScheduleSummary(schedule);

  return range ? `${summary}（${range}）` : summary;
}

export function formatYen(amount: number): string {
  return `${amount.toString().replace(/\B(?=(\d{3})+(?!\d))/gu, ",")}円`;
}

export function formatCostAmount(cost: Cost): string {
  if (cost.amountMaxYen === null || cost.amountMaxYen === cost.amountMinYen) {
    return formatYen(cost.amountMinYen);
  }

  return `${formatYen(cost.amountMinYen)}〜${formatYen(cost.amountMaxYen)}`;
}

/** The free-text label, with the fixed cost type added when the label does not already say it. */
export function formatCostLabel(cost: Cost): string {
  const typeLabel = COST_TYPE_LABELS[cost.costType];

  if (!cost.label) {
    return typeLabel;
  }

  return cost.label.includes(typeLabel) ? cost.label : `${cost.label}（${typeLabel}）`;
}

export function formatClockTime(date: Date): string {
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");

  return `${hours}:${minutes}`;
}

export function formatLastUpdated(date: Date): string {
  return `最終更新 ${formatClockTime(date)}`;
}
