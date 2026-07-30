# health-coach

This Fork adapts the upstream health-coach Skill for a private Panacea health
Wiki. It supports meal photo or text analysis, nutrition-label transcription,
longitudinal records, and evidence-based health information.

## What Changed

- Health data is written only to `WIKI_PATH`, never to a repository-local
  `health/` directory.
- Packaged-food labels and net content supplied by the user take priority.
- Photo-only portions are ranges with confidence, not precise measurements.
- Every calculated nutrition value requires a traceable source and access date.
- Daily totals are compared only with targets explicitly supplied by the user or
  clinician.
- Medical questions require evidence-based sources and do not provide diagnosis,
  prescriptions, or medication dose changes. Traditional Chinese medicine is out
  of scope.

The upstream static tables remain in repository history but are not authoritative
data sources for this Fork. See `references/evidence-sources.md`.

## Initialize a Private Wiki

```sh
WIKI_PATH=/path/to/private-health-wiki bash scripts/init.sh
```

The script creates only missing folders and templates. It never overwrites an
existing record or calculates an individualized diet target.

## Meal Records

Use `templates/meal-record.md` for one meal and
`templates/daily-nutrition.md` for its cumulative daily summary. Record source,
portion range, confidence, energy, protein, carbohydrate, fat, fiber, saturated
fat, and sodium when supported by the source.

## Attribution and License

This is a Fork of [H1an1/health-coach](https://github.com/H1an1/health-coach),
distributed under the upstream MIT License. The original project and its
contributors are credited in the Git history.
