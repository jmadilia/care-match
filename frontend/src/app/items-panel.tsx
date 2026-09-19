"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createItem, type Item } from "@/lib/api";

type Props = {
  initialItems: Item[];
  initialError: string | null;
};

export function ItemsPanel({ initialItems, initialError }: Props) {
  const router = useRouter();
  const [name, setName] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    await createItem({ name });
    setName("");
    router.refresh();
  };

  return (
    <div className="w-full max-w-md rounded-lg border border-black/[.08] p-6 dark:border-white/[.145]">
      <h2 className="mb-4 text-lg font-semibold">Items (from FastAPI + Postgres)</h2>

      <form onSubmit={handleSubmit} className="mb-4 flex gap-2">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="New item name"
          className="flex-1 rounded border border-black/[.08] bg-transparent px-3 py-2 text-sm dark:border-white/[.145]"
        />
        <button
          type="submit"
          className="rounded bg-foreground px-4 py-2 text-sm text-background hover:bg-[#383838] dark:hover:bg-[#ccc]"
        >
          Add
        </button>
      </form>

      {initialError && <p className="text-sm text-red-500">{initialError}</p>}
      {!initialError && initialItems.length === 0 && (
        <p className="text-sm text-zinc-500">No items yet — add one above.</p>
      )}

      <ul className="flex flex-col gap-2">
        {initialItems.map((item) => (
          <li key={item.id} className="rounded border border-black/[.08] px-3 py-2 text-sm dark:border-white/[.145]">
            {item.name}
          </li>
        ))}
      </ul>
    </div>
  );
}
