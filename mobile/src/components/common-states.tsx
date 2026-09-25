import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";

interface StateFrameProps {
  accessibilityLabel: string;
  action?: React.ReactNode;
  children?: React.ReactNode;
  description?: string;
  role?: "alert" | "progressbar";
  title: string;
}

function StateFrame({
  accessibilityLabel,
  action,
  children,
  description,
  role,
  title,
}: StateFrameProps) {
  return (
    <View style={styles.container}>
      <View
        accessible
        accessibilityLabel={accessibilityLabel}
        accessibilityRole={role}
        style={styles.content}
      >
        <Text accessibilityRole="header" style={styles.title}>
          {title}
        </Text>
        {description ? <Text style={styles.description}>{description}</Text> : null}
        {children}
      </View>
      {action}
    </View>
  );
}

export interface LoadingStateProps {
  label?: string;
}

export function LoadingState({ label = "読み込み中です" }: LoadingStateProps) {
  return (
    <StateFrame
      accessibilityLabel={label}
      role="progressbar"
      title={label}
    >
      <ActivityIndicator
        accessibilityElementsHidden
        color="#16775D"
        style={styles.indicator}
      />
    </StateFrame>
  );
}

export interface EmptyStateProps {
  actionLabel?: string;
  description: string;
  onAction?: () => void;
  title: string;
}

export function EmptyState({
  actionLabel,
  description,
  onAction,
  title,
}: EmptyStateProps) {
  return (
    <StateFrame
      accessibilityLabel={`${title}。${description}`}
      action={
        actionLabel && onAction ? (
          <StateAction label={actionLabel} onPress={onAction} />
        ) : null
      }
      description={description}
      title={title}
    />
  );
}

export interface ErrorStateProps {
  description: string;
  onRetry?: () => void;
  requestId?: string;
  retryLabel?: string;
  title?: string;
}

export function ErrorState({
  description,
  onRetry,
  requestId,
  retryLabel = "再試行",
  title = "読み込めませんでした",
}: ErrorStateProps) {
  const requestIdDescription = requestId
    ? `問い合わせID: ${requestId}`
    : undefined;

  return (
    <StateFrame
      accessibilityLabel={`${title}。${description}`}
      action={
        onRetry ? <StateAction label={retryLabel} onPress={onRetry} /> : null
      }
      description={description}
      role="alert"
      title={title}
    >
      {requestIdDescription ? (
        <Text selectable style={styles.metadata}>
          {requestIdDescription}
        </Text>
      ) : null}
    </StateFrame>
  );
}

export interface OfflineStateProps {
  description?: string;
  lastUpdatedLabel?: string;
  title?: string;
}

export function OfflineState({
  description = "インターネット接続を確認してください。",
  lastUpdatedLabel,
  title = "オフラインです",
}: OfflineStateProps) {
  return (
    <StateFrame
      accessibilityLabel={`${title}。${description}`}
      description={description}
      role="alert"
      title={title}
    >
      {lastUpdatedLabel ? (
        <Text style={styles.metadata}>{lastUpdatedLabel}</Text>
      ) : null}
    </StateFrame>
  );
}

interface StateActionProps {
  label: string;
  onPress: () => void;
}

function StateAction({ label, onPress }: StateActionProps) {
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      style={styles.action}
    >
      <Text style={styles.actionLabel}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
  },
  content: {
    alignItems: "center",
  },
  title: {
    color: "#17201D",
    fontSize: 20,
    fontWeight: "700",
    textAlign: "center",
  },
  description: {
    marginTop: 8,
    color: "#59635F",
    fontSize: 15,
    lineHeight: 22,
    textAlign: "center",
  },
  indicator: {
    marginTop: 16,
  },
  metadata: {
    marginTop: 10,
    color: "#6D7672",
    fontSize: 13,
    textAlign: "center",
  },
  action: {
    minHeight: 48,
    marginTop: 16,
    justifyContent: "center",
    borderRadius: 8,
    backgroundColor: "#16775D",
    paddingHorizontal: 20,
  },
  actionLabel: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "700",
  },
});
