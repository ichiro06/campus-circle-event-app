import { getEvents } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function EventsPage() {
  const events = await getEvents();

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <div className="mb-8">
        <p className="text-sm font-semibold text-green-700">Event Board</p>
        <h1 className="mt-2 text-3xl font-bold">イベント告知</h1>
        <p className="mt-3 text-gray-600">
          体験会、ライブ、説明会など、学生団体のイベント情報を一覧できます。
        </p>
      </div>

      <div className="grid gap-4">
        {events.map((event) => (
          <article key={event.id} className="rounded border border-gray-200 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-xl font-semibold">{event.title}</h2>
              <span className="rounded bg-green-50 px-2 py-1 text-sm text-green-700">
                {event.type}
              </span>
            </div>
            <p className="mt-2 text-sm text-gray-600">{event.circleName}</p>
            <p className="mt-3 text-gray-700">{event.description}</p>
            <dl className="mt-3 space-y-1 text-sm text-gray-600">
              <div>
                <dt className="inline font-semibold">日時: </dt>
                <dd className="inline">{event.startsAt}</dd>
              </div>
              <div>
                <dt className="inline font-semibold">場所: </dt>
                <dd className="inline">{event.place}</dd>
              </div>
            </dl>
            <div className="mt-3 flex flex-wrap gap-2">
              {event.tags.map((tag) => (
                <span key={tag} className="rounded bg-gray-100 px-2 py-1 text-sm">
                  {tag}
                </span>
              ))}
            </div>
          </article>
        ))}
      </div>
    </main>
  );
}
