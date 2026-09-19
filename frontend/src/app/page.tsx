import { getItems, type Item } from "@/lib/api";
import { ItemsPanel } from "./items-panel";

export default async function Home() {
  let items: Item[] = [];
  let error: string | null = null;

  try {
    items = await getItems();
  } catch {
    error =
      "Could not reach the backend. Is it running at NEXT_PUBLIC_API_URL (default http://localhost:8000)?";
  }

  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-8 bg-zinc-50 px-6 py-24 font-sans dark:bg-black">
      <div className="text-center">
        <h1 className="text-3xl font-semibold tracking-tight">
          Next.js + FastAPI + Postgres
        </h1>
        <p className="mt-2 text-zinc-600 dark:text-zinc-400">
          Edit <code className="rounded bg-black/[.06] px-1.5 py-0.5 font-mono text-[0.9em] dark:bg-white/[.08]">frontend/src/app/page.tsx</code> to get started.
        </p>
      </div>
      <ItemsPanel initialItems={items} initialError={error} />
    </div>
  );
}
