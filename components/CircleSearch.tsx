"use client";

import { useMemo, useState } from "react";
import type { Circle } from "@/lib/campusData";

type Props = {
  circles: Circle[];
};

export default function CircleSearch({ circles }: Props) {
  const [keyword, setKeyword] = useState("");
  const [category, setCategory] = useState("all");

  const categories = useMemo(
    () => ["all", ...Array.from(new Set(circles.map((circle) => circle.category)))],
    [circles],
  );

  const filteredCircles = useMemo(() => {
    const normalizedKeyword = keyword.trim().toLowerCase();

    return circles.filter((circle) => {
      const matchesCategory = category === "all" || circle.category === category;
      const searchText = [
        circle.name,
        circle.category,
        circle.activityDays,
        circle.place,
        circle.description,
        ...circle.tags,
      ]
        .join(" ")
        .toLowerCase();

      return matchesCategory && searchText.includes(normalizedKeyword);
    });
  }, [category, circles, keyword]);

  return (
    <section className="space-y-6">
      <div className="grid gap-3 md:grid-cols-[1fr_180px]">
        <input
          className="rounded border border-gray-300 px-3 py-2"
          value={keyword}
          onChange={(event) => setKeyword(event.target.value)}
          placeholder="サークル名・タグ・活動場所で検索"
        />
        <select
          className="rounded border border-gray-300 px-3 py-2"
          value={category}
          onChange={(event) => setCategory(event.target.value)}
        >
          {categories.map((item) => (
            <option key={item} value={item}>
              {item === "all" ? "すべて" : item}
            </option>
          ))}
        </select>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {filteredCircles.map((circle) => (
          <article key={circle.id} className="rounded border border-gray-200 p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="text-xl font-semibold">{circle.name}</h2>
                <p className="text-sm text-gray-600">
                  {circle.category} / {circle.official ? "公認" : "非公認"}
                </p>
              </div>
              <span className="rounded bg-gray-100 px-2 py-1 text-sm">
                {circle.recruiting ? "募集中" : "募集停止中"}
              </span>
            </div>
            <p className="mt-3 text-gray-700">{circle.description}</p>
            <dl className="mt-3 space-y-1 text-sm text-gray-600">
              <div>
                <dt className="inline font-semibold">活動日: </dt>
                <dd className="inline">{circle.activityDays}</dd>
              </div>
              <div>
                <dt className="inline font-semibold">場所: </dt>
                <dd className="inline">{circle.place}</dd>
              </div>
            </dl>
            <div className="mt-3 flex flex-wrap gap-2">
              {circle.tags.map((tag) => (
                <span key={tag} className="rounded bg-blue-50 px-2 py-1 text-sm text-blue-700">
                  {tag}
                </span>
              ))}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
