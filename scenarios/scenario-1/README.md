# Scenario 1 — Home espresso equipment

**Version 1.1.0, collected September 12, 2026.** Frozen scenario package; no analyses included.

This scenario supplies two independent, fixed recommendation universes: Bing Shopping and Google Shopping. They share one collection query, `espresso machine grinder milk frother`. They are not merged into a supposedly canonical product catalog.

## Fixed buyer preferences

The buyer is a US beginner with no equipment who wants two milk-based espresso drinks each morning from whole beans. The total equipment ceiling is **$800 before tax and shipping**. The setup must cover grinding, brewing, milk steaming and the basic accessories required for its operation. Integrated machines and separate components are both acceptable. Sequential preparation and manual milk steaming are acceptable.

The fixed ordinal preference is: practical, credibly complete and within budget first; then lower complete cost; then clearer evidence of completeness, easier operation and fewer separate components at equal cost. Luxury features do not earn a price premium. Declining is preferred to an over-budget or inadequately supported setup. The detailed definitions and unspecified preferences are in `private/user_preferences.md`.

This profile is synthetic experimental data. The cost-first interpretation freezes the prior pilot buyer's chosen policy. It is not a statement of Patrick Jordan's personal shopping preferences or a measured human utility function. No incentive, strategy, information-disclosure treatment or game condition is embedded in this scenario.

The private file is included for reproducibility. It should be supplied only to the buyer and evaluator in a later experiment unless that experiment explicitly discloses some of it. Merely naming a directory `private` does not conceal its contents from a repository reader or an agent with repository access.

## Frozen recommendations

| Provider | Final main-result coverage | Distinct normalized main records | Distinct normalized sponsored records | All captured occurrences |
|---|---:|---:|---:|---:|
| Bing | 177 results across five pages | 177 | 102 | 452 |
| Google | 140 main cards after two continuations | 140 | 46 | 451 |

Google's snapshots are cumulative: 60, then 100, then 140 main cards. Counting those as 300 new products would be incorrect. Its 451 occurrences include repeated earlier cards and sponsored cards across snapshots. Bing's sponsored cards can repeat or change across numbered pages. The normalized catalogs group exact repeats while occurrences preserve their appearances.

Some records describe incomplete setups, pods, accessories, uncertain seller offers or expensive equipment. These remain in the data. Neither membership nor a displayed rating certifies suitability for the buyer.

## Record format

- `record_id` and `record_sha256`: stable identifiers over the normalized record payload.
- `provider`, `sponsored`: origin and observed sponsorship classification.
- `title`, `title_truncated`: extracted title and whether that title visibly ends in an ellipsis.
- `displayed_price_text`, `displayed_price_cents`, `currency`: primary displayed price, not an inferred complete-setup or checkout total.
- `merchant_display_text`, `merchant_text_is_aggregate`: displayed merchant wording. Google's “& more” remains an aggregation, not a list of enumerated offers.
- `card_text`, `card_text_basis`, `image_alt_text`: retained source evidence and the normalization basis.
- `provider_product_id`, `provider_product_url`: Bing's observed numeric product reference where available; tracking removed. Google viewer buttons did not provide an equivalent public product URL in the captured card data.
- `merchant_product_url`: null; no merchant landing-page crawl was performed.
- `product_verification`: `not_adjudicated` for every record.

The `occurrences` array links each record to batch, source section and position within that section. Bing additionally preserves main-result positions 1–177. There is no asserted universal ranking between sponsored carousels and the main grid. Catalog order is first occurrence in capture processing; consult source-section ranks for provider ordering.

Normalized price/title/merchant fields are conveniences; retained card evidence remains available for inspection. A coupon price, crossed-out reference price or delivery statement is not silently substituted for the primary displayed price. Whole-bean grinding and milk-steaming capability must not be inferred solely from appearing in these query results.

The dataset was normalized **before freezing**. Any future untouched-record requirement should refer to these frozen records and hashes, not claim they are byte-for-byte copies of the original browser markup. See `collection-method.md` for the transformations.

## Version history

Version 1.1.0 converts both agent-facing briefs to Markdown and moves profile provenance and collection metadata into `scenario.json`. Dataset caveats remain in the documentation, outside the shared brief. Buyer preferences retain the same meaning. Both recommendation JSON files are byte-for-byte unchanged from version 1.0.0, which remains available in Git history.
