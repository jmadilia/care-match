// 127.0.0.1 (not "localhost") avoids Node's fetch trying an IPv6 route to a
// backend that only listens on IPv4.
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export type Item = {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
};

export async function getItems(): Promise<Item[]> {
  const res = await fetch(`${API_URL}/api/v1/items`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch items: ${res.status}`);
  return res.json();
}

export async function createItem(input: { name: string; description?: string }): Promise<Item> {
  const res = await fetch(`${API_URL}/api/v1/items`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) throw new Error(`Failed to create item: ${res.status}`);
  return res.json();
}
