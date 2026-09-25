import { ShellScreen } from "@/components/shell-screen";

export default function MyPageScreen() {
  return (
    <ShellScreen
      description="マイページを使うにはログインまたは新規登録が必要です。"
      eyebrow="LOGIN REQUIRED"
      title="マイページ"
    />
  );
}
