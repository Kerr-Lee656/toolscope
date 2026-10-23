# Editorial criteria

The rules behind what appears on [toolscope.app](https://toolscope.app).

## 1. Usefulness

The only question that matters. For each candidate:

- Does it solve a specific problem a developer or knowledge worker actually has?
- Is it usable today — installable, reachable, documented enough to start?
- Is it maintained, or at least complete enough that lack of maintenance is not fatal?

If the answer to the first question is no, the candidate is rejected no matter how
many stars it has.

## 2. Established

For GitHub projects: `stars >= 100`.

This is a floor, not a ranking criterion. There is no ceiling, and star count never
substitutes for usefulness.

## 3. Not excluded

| Excluded | Example |
|---|---|
| Tutorial collections posing as tools | "100 days of X" repos with no runnable software |
| Personal configuration | dotfiles, personal notes, resume repos |
| Empty or archived | no meaningful commits in a year, or archive flag set |
| Unreachable | dead links, deleted repositories, gated without public access |

## 4. Review outcomes

```
accept   →  enriched and published
review   →  held in the candidate pool for a human decision
reject   →  archived with a reason, never published
```

Rejections are archived rather than dropped, so a project that improves later can be
reevaluated instead of rediscovered.

## 5. Enrichment

Published entries are written, not scraped. Each carries:

- `summary` — what it is, in two sentences
- `intro` — what problem it solves, for whom
- `audience` — who should care
- `cost` — pricing model, including "free" stated explicitly
- `difficulty` — realistic starting effort
- `quick_start` — the shortest path to a first result
- `pros` / `cons` — honest, including limitations the project's own README omits

All of the above exist in Chinese and English as independent fields, validated in CI.

## 6. Corrections

If an entry becomes stale — project archived, pricing changed, domain expired — it is
updated or removed rather than left to rot. The directory's value is that being listed
still means something.
