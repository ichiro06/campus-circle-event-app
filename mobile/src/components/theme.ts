// Shared with the existing shell and common-state components (#16775D / #17201D / #59635F).
export const colors = {
  accent: "#16775D",
  accentSoft: "#E3F2EC",
  background: "#F7F8FA",
  border: "#D9DEDB",
  danger: "#9C2F2F",
  surface: "#FFFFFF",
  textMuted: "#59635F",
  textPrimary: "#17201D",
  textSubtle: "#6D7672",
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
} as const;

/** 48 satisfies both iOS (44pt) and Android (48dp) minimum tap targets. */
export const MIN_TAP_TARGET = 48;
