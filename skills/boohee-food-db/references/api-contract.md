# Boohee Food API Contract

Official documentation: https://ai.boohee.com/docs/

- Base URL: `https://api.boohee.com/open-apis`
- Authentication: `X-Api-Key: ${BOHE_NUTRITION_API_KEY}`
- Common response: JSON with `code`, `message`, `now`, and `data`; `code: 0`
  indicates success.

## Used Endpoints

| Operation | Method and path | Key inputs |
| --- | --- | --- |
| Search | `GET /v1/food/search` | `keyword` or 13-digit `barcode`, `page`, `per_page`, `with_units` |
| Detail | `GET /v1/food/detail` | `code`, optional `with_ingredients`, `with_units`, `with_materials` |
| Category list | `GET /v1/food/list` | `id`, `kind`, optional `with_units` |
| Meal nutrients | `POST /v1/food/ingredients` | `foods`: code+gram weight or barcode+count |

The search endpoint accepts 1-30 character keywords, defaults to 20 records per
page, and allows at most 50. The batch nutrient endpoint is used only after food
identity and portion are confirmed; it reduces remote-call use for a meal.

Never call state-changing food, diet, body-weight, recipe, account, or image
recognition endpoints from this Skill.

## Source Aggregation

Use this API alongside, not instead of, authoritative web research. Package labels
supplied by the user take precedence. For unlabelled food, compare the Boohee value
with a manufacturer, restaurant, regulator, or authoritative food-composition
source on the same per-100g or serving basis. Do not average conflicts; retain both
provenance records and explain the uncertainty. An exhausted daily quota or API
failure switches the lookup to the web source without retrying the API.
