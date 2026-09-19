export default function Home() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-4 bg-zinc-50 px-6 py-24 font-sans dark:bg-black">
      <div className="text-center">
        <h1 className="text-3xl font-semibold tracking-tight">Care Match</h1>
        <p className="mt-2 text-zinc-600 dark:text-zinc-400">
          Therapist-client matching and waitlist optimization engine. Domain UI coming soon.
        </p>
      </div>
    </div>
  );
}
