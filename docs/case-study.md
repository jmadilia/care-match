# Care Match: case study

Live demo: [care-match-three.vercel.app](https://care-match-three.vercel.app/) · Code: [github.com/jmadilia/care-match](https://github.com/jmadilia/care-match)

## Summary

Care Match is a therapist-client matching and waitlist optimization engine, built on synthetic data. It asks a question that sits underneath every telehealth marketplace: given a limited, unevenly distributed supply of licensed, insurance-paneled clinicians and a stream of clients with different needs and urgency, who should be matched to whom?

I built four matching strategies (greedy, stable matching, optimal assignment, and a waitlist that prioritizes by urgency and time waited), ran them against identical simulated populations, and compared them on fill rate, match quality, provider load balance, and fill rate by urgency. The finished system is a FastAPI backend, a Next.js frontend with two interactive pages, and a Postgres database, deployed publicly on Vercel and Neon.

The headline finding is that no strategy wins outright. Optimal assignment serves the most clients (91.4%). Stable matching produces the best average match quality. Only the waitlist strategy lets urgency change who gets served: it fills 95.5% of urgent clients against 80.3% of routine ones, but it pays for that with lower overall fill and lower average match quality.

## The problem

Matching a client to a therapist looks like a lookup: filter providers by state and insurance, sort by fit, pick the first. That works until supply is constrained, and in mental health it always is. Each provider is licensed in only some states, paneled with only some insurers, and capped at a weekly caseload. Picking the best available provider for each client in arrival order overloads the popular clinicians, leaves others idle, and quietly strands clients whose only eligible provider was used up by someone who had other options.

So I treated it as a two-sided marketplace problem and set out to measure how much the choice of strategy matters, instead of assuming one approach was right.

## Design decisions

**Compare strategies on the same population, each in its own universe.** The comparison is only meaningful if every strategy sees identical clients and providers. A synthetic generator produces a population from a seed, and each strategy runs against it independently. Capacity is not a counter on the provider. It is derived at query time from the matches that hold a slot, scoped to the strategy that made them, so strategies can't consume each other's capacity. That costs more queries than a stored counter, and I chose it on purpose: a derived value can't drift out of sync with the matches it describes, and for a project whose point is trustworthy comparison, correctness mattered more than speed.

**Hard constraints versus soft scores.** Only state licensure and insurance paneling decide whether a pairing is allowed at all, because those are the real legal and billing walls. Specialty, language, and modality are a weighted fit score. This means a scarce specialty shows up as worse matches instead of as unserved clients, which matches how a real marketplace degrades.

**Four strategies, each answering a different question.**
- *Greedy* is first come, first served with no lookahead. It is the baseline and the only one that needs no knowledge of the rest of the population.
- *Stable matching* is client-proposing Gale-Shapley, with providers ranking clients by the same mutual fit score. No pair would both rather be matched to each other than to their assignments.
- *Optimal* is the Hungarian algorithm over the whole batch, maximizing total match score. Provider capacity becomes slot columns, and each client gets a zero-cost "unmatched" column so a client can be left out when that is globally better.
- *Waitlist priority* simulates clients arriving day by day over a 28-day horizon. A provider admits by priority (an urgency baseline plus half a point per day waited) and can bump a lower-priority holder when a more urgent client arrives. Bumped clients re-enter the pool.

**Choosing the scenario from data, not instinct.** I swept the demand-to-capacity ratio from 0.7 to 1.25 and measured the gap between a naive greedy pass and the best possible assignment. It peaked at 1.0, so that is the ratio the reported results use: the point where the choice of strategy matters most. There are also scenarios with an undersupplied state and a scarce specialty.

**Anchored, honest synthetic data.** The generator's distributions follow public sources where they exist (Census state shares, workforce data on Spanish-speaking providers, studies on Medicaid acceptance) and are labeled as assumptions where they don't. Every weight lives in one config file.

## A bug worth telling

Early on, the same seed produced slightly different results on different runs. The cause was subtle: every row in a bulk insert shares one transaction timestamp, so ordering by `created_at` left ties that Postgres was free to break differently on different queries. The fix was to tie-break on `name` everywhere, plus a regression test that generates two separate populations from one seed and requires every strategy to return identical summaries. I found it by running the same comparison twice and diffing the output, which is also how I'd recommend finding the next one.

## Making a simulation safe to put on the public internet

Running a heavy computation behind an open endpoint is the interesting part of this project from a systems point of view.

- **Nothing a visitor does is stored.** Comparison and intake run inside a scratch session: a connection, an outer transaction, and a session joined to it with savepoints, always rolled back. Visitors can generate thousands of rows of synthetic data and the database ends up empty. The test suite and the comparison harness use the same mechanism, and one test asserts no rows are left behind.
- **Requests are capped.** Seeds, providers, clients, and total client-runs all have limits, so one request can't ask for unbounded work.
- **Results are cached exactly.** Because every strategy is deterministic for a seed, a comparison is a pure function of its request, so caching is exact instead of approximate. The default result is served from a committed snapshot (about 50 seconds computed, 0.18s served live). Other requests go through an in-memory cache, then a bounded table in Postgres that all serverless instances share, keyed by the request and the deployed commit so a code change can't serve stale results. Identical concurrent requests on one instance share a single computation.
- **The admin API fails closed.** The CRUD and strategy-run endpoints are mounted only when `ENVIRONMENT=local`. Elsewhere they are not mounted at all, so they return 404 instead of relying on authentication, and enabling them requires an API key or the app refuses to start.
- **Serverless Postgres details.** No connection pool inside short-lived instances (the database's pooler does that job), prepared statements off for transaction-mode pooling, a pooled URL for the app, and a direct URL for migrations.

## What went wrong on the first deploy

The first deployment had two problems, and I think they are worth recording honestly. The admin routes were publicly mounted, because `ENVIRONMENT` was unset and defaulted to local. I caught it in the first smoke test, which probes a route that should be 404, and the database had no tables yet, so nothing could be written. Separately, the intake and comparison endpoints returned 500s because the migrations had been run against a different database than Production used. The runtime traceback named the missing table in one read. Both fixes were configuration, not code. The lesson I took is to make the failure loud and the smoke test specific: after any deploy, check that what should be closed is closed, not only that what should be open works.

## Results

Balanced scenario, 60 providers, 300 clients, averaged over 10 seeds:

| Strategy | Fill rate | Mean match score | Provider load stdev | Routine / elevated / urgent fill |
|---|---|---|---|---|
| Greedy | 85.7% | 0.865 | 0.250 | 85.0% / 86.1% / 91.0% |
| Stable matching | 83.0% | 0.889 | 0.298 | 82.7% / 83.7% / 83.8% |
| Optimal | 91.4% | 0.884 | 0.211 | 91.1% / 91.9% / 93.7% |
| Waitlist priority | 83.8% | 0.837 | 0.295 | 80.3% / 93.8% / 95.5% |

Three takeaways:
1. **Optimal wins on throughput and balance, not on quality.** It serves more clients and spreads load best by accepting some lower-quality matches that the other strategies decline to make.
2. **Stable matching concentrates demand.** Its matches are the best on average, but they pile onto the providers everyone already prefers.
3. **Urgency only matters if the strategy can see it.** The first three never look at urgency, so their small urgent-versus-routine gaps are incidental. The waitlist strategy's 15-point gap is causal, and it is explicitly traded against overall fill and average match quality. That is a policy decision a real marketplace would make deliberately.

## What I would do next

The [README](../README.md#limitations) lists the limitations in full. The ones I would tackle first: provider capacity never renews, so time-to-match and churn aren't modeled; the scoring weights and urgency baselines are tuned rather than fitted, and their sensitivity is unexplored; and results aren't broken out by payer or language, so whether Medicaid or Spanish-speaking clients fare worse under each strategy is an open question the data could answer. Adding provider-side preferences, so "stable" means something more than a shared fit score, is the change I think would teach the most.

## Stack and numbers

Next.js (App Router, TypeScript, Tailwind) · FastAPI, SQLAlchemy 2.0, Alembic, Pydantic · PostgreSQL (Neon in production) · uv, pytest, ruff, mypy (strict) · GitHub Actions on every push · Vercel Services for a one-project deployment.

158 backend tests, covering each strategy, the generator, determinism, the API lockdown, the caches, and the no-leftover-rows guarantee.
