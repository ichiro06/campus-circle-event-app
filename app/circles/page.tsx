import CircleSearch from "@/components/CircleSearch";
import { getCircles } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function CirclesPage() {
  const circles = await getCircles();

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <div className="mb-8">
        <p className="text-sm font-semibold text-blue-700">Circle Search</p>
        <h1 className="mt-2 text-3xl font-bold">サークルを探す</h1>
        <p className="mt-3 text-gray-600">
          公認・非公認を問わず、活動内容やタグから自分に合う団体を探せます。
        </p>
      </div>
      <CircleSearch circles={circles} />
    </main>
  );
}
