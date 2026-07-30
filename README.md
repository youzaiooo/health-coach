# health-coach

This Fork is a focused extension for Panacea, not a replacement health agent. It
provides only three capabilities:

- Meal analysis from photos, descriptions, menus, and package labels.
- Weight and body-measurement records with transparent trends.
- Evidence-based supplement review and user-reported supplement tracking.

Medical questions, laboratory reports, symptoms, prescribed medicines, emergency
guidance, and personal-Wiki governance remain with Panacea's existing SOUL and
Skills. The Fork must not override those rules.

## Operating Principles

- Store personal data only under `WIKI_PATH`.
- Use package labels and net content before any image estimate.
- Express image-only portions as ranges with confidence.
- Attach a source and access date to calculated nutrition values.
- Do not set nutrition targets, prescribe diets, diagnose, prescribe, or adjust a
  medicine or supplement dose.

## Initialize a Private Wiki

```sh
WIKI_PATH=/path/to/private-health-wiki bash scripts/init.sh
```

The script creates missing templates only and never overwrites records.

## Attribution and License

This is a Fork of [H1an1/health-coach](https://github.com/H1an1/health-coach),
distributed under the upstream MIT License. The original project and its
contributors are credited in the Git history.
