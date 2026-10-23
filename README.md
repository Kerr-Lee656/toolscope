# ToolScope — data-quality tooling

Tooling and editorial rules behind [toolscope.app](https://toolscope.app), a curated
directory of **7,274** open-source projects and online tools across **35** categories.

This repository holds the parts of the pipeline that define *what gets published* —
the inclusion rules, the bilingual validation checks, and the slug normalisation —
so the editorial standard is inspectable rather than implied.

The application itself, the dataset, and the enrichment models stay private.

---

## Inclusion rules

A candidate is published only when **both** hold:

| Rule | Detail |
|---|---|
| **Useful** | An LLM review answers *would a working developer get value from this?* Candidates scoring reject are archived with a reason, not deleted |
| **Established** | `stars >= 100` for GitHub projects. Online tools and browser extensions are judged on the usefulness rule alone |

There is deliberately **no upper star bound** and **no AI-only filter**. A widely
used non-AI developer resource belongs in the directory exactly as much as a niche
AI agent framework does.

Excluded regardless of popularity: tutorials masquerading as tools, personal dotfile
repos, empty or archived repositories, and anything that cannot be reached.

Measured rejection rate across reviewed candidates: **21.6%**.

## Bilingual completeness

Every published entry carries Chinese and English for `summary`, `intro`,
`audience`, `cost`, `difficulty`, `quick_start`, and `pros`/`cons`. The English site
is not a translation layer added at render time — it is a separate field set that is
validated in CI.

`scripts/check_i18n.py` fails the build when:

- an English field contains Han characters
- a required bilingual field is missing on one side
- a locale file leaked UI copy into a data field

## Slugs

Stable, readable, and collision-free. `scripts/slug_util.py` normalises names
(including CJK), strips hostnames down to a readable stem, and appends a
disambiguating path segment when a bare word would collide across categories.

A slug never changes after publication — inbound links and search rankings depend
on it.

## Layout

```
scripts/
  check_i18n.py    bilingual completeness and leakage checks
  slug_util.py     slug normalisation, collision handling
docs/
  editorial.md     the review criteria in full
```

## Running

```bash
python scripts/check_i18n.py --lib path/to/data
```

Both scripts are stdlib-only and read data from a sibling `src/lib` directory by
default.

---

<sub>Maintained by [Kerr Lee](https://github.com/Kerr-Lee656) · [toolscope.app](https://toolscope.app)</sub>
