import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Campus Circle API Technical Verification",
  description: "モバイル製品向けFastAPIの表示確認用ページ",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
