import Link from "next/link";

export default function Home() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-6 bg-zinc-50 px-6 py-24 font-sans dark:bg-black">
      <div className="text-center">
        <h1 className="text-3xl font-semibold tracking-tight">Care Match</h1>
        <p className="mt-2 text-zinc-600 dark:text-zinc-400">
          Therapist-client matching and waitlist optimization engine.
        </p>
      </div>
      <nav className="flex gap-4">
        <Link
          href="/comparisons"
          className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white dark:bg-white dark:text-black"
        >
          Strategy comparison
        </Link>
        <Link
          href="/intake"
          className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium dark:border-zinc-700"
        >
          Client intake
        </Link>
      </nav>
    </div>
  );
}
