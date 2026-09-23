import { StyleSheet, Text, View } from "react-native";

export interface ShellScreenProps {
  description: string;
  eyebrow?: string;
  title: string;
}

export function ShellScreen({
  description,
  eyebrow = "CAMPUS CIRCLE",
  title,
}: ShellScreenProps) {
  return (
    <View style={styles.container}>
      <View style={styles.mark} accessibilityElementsHidden />
      <Text style={styles.eyebrow}>{eyebrow}</Text>
      <Text accessibilityRole="header" style={styles.title}>
        {title}
      </Text>
      <Text style={styles.description}>{description}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#F7F8FA",
    paddingHorizontal: 24,
  },
  mark: {
    width: 48,
    height: 6,
    marginBottom: 24,
    borderRadius: 3,
    backgroundColor: "#16775D",
  },
  eyebrow: {
    color: "#16775D",
    fontSize: 13,
    fontWeight: "700",
  },
  title: {
    marginTop: 10,
    color: "#17201D",
    fontSize: 28,
    fontWeight: "700",
    textAlign: "center",
  },
  description: {
    marginTop: 12,
    color: "#59635F",
    fontSize: 15,
    lineHeight: 22,
    textAlign: "center",
  },
});
