---
name: health-coach
description: Analyze meals, weight trends, and supplements with sources.
---

# Health Coach

Provide three focused capabilities for Panacea: meal analysis, weight tracking,
and supplement review. Follow Panacea's SOUL for medical evidence, safety,
privacy, and personal-Wiki governance. This skill does not replace those rules.

## Storage and Privacy

- Require `WIKI_PATH` before writing. For Panacea, it is the private health Wiki.
- Store health data only below `WIKI_PATH`; never create a parallel `health/`
  directory and never commit personal data to this repository.
- Preserve original files in `raw/` when the user provides a report or image.
- Separate user statements, label transcriptions, image observations, calculations,
  and clinical interpretation in every record.
- Do not create or change personal nutrition targets until the user or clinician
  supplies them. Do not infer age, sex, body metrics, disease status, or medication.

Initialize an empty Wiki safely with:

```sh
WIKI_PATH=/path/to/private-health-wiki bash scripts/init.sh
```

The script only creates missing directories and templates. It never overwrites
existing records or calculates a diet prescription.

## Meal Workflow

For every meal photo, food description, menu, or package label:

1. Identify foods and separate packaged items, single ingredients, and mixed dishes.
2. Transcribe a visible nutrition label and net content exactly when supplied. Treat
   this as the primary nutrition source for that product.
3. For foods without a label, aggregate two traceable sources: load
   `boohee-food-db` to use its private Wiki cache or the Boohee API, and use
   `web_search` plus `web_extract` to obtain an official manufacturer, restaurant,
   or authoritative food-composition source. Record the URL or citation and access
   date. Do not use search snippets, lifestyle articles, or uncited database entries
   as numeric sources.
4. Compare only values with the same basis (for example, per 100g or the same
   labelled serving). Do not average mismatched or materially conflicting values.
   Prefer a user-provided package label, then the product's official source. State
   any unresolved discrepancy and keep both source trails.
5. If Boohee has no match, its daily quota is exhausted, or the API fails, continue
   with the authoritative web source and label the result as web-derived rather than
   silently inventing a replacement value.
6. Estimate a photo-only portion as a range, not a precise weight. State the visual
   anchors used (container, utensils, known package size, or plate dimensions) and
   mark confidence `high`, `medium`, or `low`.
7. For a mixed cooked dish, list its visible components and give a wider range. Ask
   for the key missing facts when they would materially change the result: recipe,
   oil, sauces, sugar, edible portion, package net content, or serving count.
8. Calculate the best estimate and range for energy, protein, carbohydrate, total
   fat, fiber, saturated fat, and sodium when the source supports them. Never invent
   missing micronutrients or pretend an image provides laboratory precision.
9. Save the meal using `templates/meal-record.md` under
   `records/meals/YYYY-MM-DD-HHMM-short-name.md`. Rebuild that date's cumulative
   totals with `templates/daily-nutrition.md` under `records/daily/` without
   deleting user notes.
10. Compare totals with an explicit user- or clinician-provided target only. Otherwise
   report totals and state that no individualized target is on file.

Present the result with the food table first, then uncertainty, cited sources, and
one or two practical next steps. Do not present an estimated value as a measured
value.

## Weight Tracking

When the user provides a weight, waist circumference, or body-composition value:

1. Record the reported value, unit, date, measurement conditions, and source in
   `records/measurements/` using `templates/weight-record.md`.
2. Preserve all raw measurements. Calculate a trend only from dated observations;
   identify the time window and do not treat a short-term change as body-fat change.
3. Show the trend and data gaps. Compare it with a user- or clinician-defined goal
   only when one exists.
4. Do not prescribe a calorie deficit, medication, or treatment in response to a
   weight trend. Route medical causes, rapid unexplained changes, and treatment
   decisions to Panacea under its SOUL.

## Supplement Review

Use this module only for a named supplement, its label, a logged dose, or a direct
supplement question:

1. Transcribe product, active ingredients, form, amount per serving, and the user's
   reported use without guessing a dose.
2. Research benefits, limitations, adverse effects, and interaction concerns using
   Panacea's evidence-first order. Prefer guidelines, systematic reviews, clinical
   trials, and regulator or manufacturer label information; cite the source used.
3. Record a durable user-reported regimen under `records/medications/` only under
   the Wiki rules in Panacea's SOUL. Clearly label it as user-reported.
4. Do not recommend starting, stopping, substituting, or changing a dose. For a
   possible drug interaction, pregnancy, kidney or liver disease, a child, or a
   serious adverse effect, direct the user to a pharmacist or clinician.

## Explicitly Out of Scope

Do not use this skill to answer general medical questions, interpret laboratory
reports, assess symptoms, discuss disease management, handle prescribed medicines,
or govern the health Wiki. Those tasks belong to Panacea itself and its existing
SOUL, `panacea-health`, `llm-wiki`, and `wiki-governance` Skills.

## Record Conventions

Use these paths when present:

| Data | Path |
| --- | --- |
| Personal baseline and preferences | `profile.md` |
| User or clinician nutrition targets | `nutrition-goals.md` |
| Individual meals | `records/meals/` |
| Daily nutrition summaries | `records/daily/` |
| Weight and body measurements | `records/measurements/` |
| User-reported supplement use | `records/medications/` |
| Original private materials | `raw/reports/`, `raw/images/`, `raw/sources/` |

Read `references/evidence-sources.md` before doing nutritional calculations or a
supplement review. The older static tables in `references/` are retained for
repository history only and are not authoritative data sources.

## Safety Boundaries

- Do not claim clinical-grade accuracy from an image.
- Do not set aggressive calorie deficits, minimum intake, or therapeutic diets by
  default.
- Do not turn generic reference ranges into a diagnosis.
- Ask before making irreversible restructures or bulk changes to the health Wiki.
