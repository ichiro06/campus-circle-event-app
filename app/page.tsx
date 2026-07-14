import Link from "next/link";

export default function Home() {
  return (
    <main className="mx-auto max-w-5xl px-6 py-12">
      <section className="space-y-6">
        <div>
          <p className="text-sm font-semibold text-blue-700">Campus Circle Event App</p>
          <h1 className="mt-3 text-4xl font-bold">サークルとイベントをまとめて探す</h1>
          <p className="mt-4 max-w-2xl text-gray-600">
            公式サイト、SNS、口コミに分散しがちな学生団体の情報を一元化し、
            新入生や途中入部希望者が探しやすい状態にするためのWebアプリです。
          </p>
        </div>

        <div className="flex flex-wrap gap-3">
          <Link
            className="rounded bg-blue-600 px-4 py-2 font-semibold text-white"
            href="/circles"
          >
            サークルを探す
          </Link>
          <Link
            className="rounded border border-gray-300 px-4 py-2 font-semibold"
            href="/events"
          >
            イベントを見る
          </Link>
        </div>
      </section>
    </main>
  );
}
