export type Circle = {
  id: number;
  name: string;
  category: string;
  official: boolean;
  activityDays: string;
  place: string;
  description: string;
  tags: string[];
  sns: string;
  recruiting: boolean;
};

export type CampusEvent = {
  id: number;
  title: string;
  circleName: string;
  startsAt: string;
  place: string;
  type: string;
  description: string;
  tags: string[];
};
