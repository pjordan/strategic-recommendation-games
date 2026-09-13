# What is in the unreturned recommendation catalog?

**Scenario 1 catalog characterization · 13 September 2026**

The short recommendation lists do **not** establish that the other 400-plus records are meaningless. The frozen catalog contains real repetition, unaffordable offers and weak descriptions, but it also contains hundreds of unreturned, within-budget alternatives. The agents selected small sets without supplying an exhaustive justification for rejecting every other record.

## Coverage: omission is much larger than obvious budget exclusion

Across the five fully validated strategic games—sole Bing, sole Google, informed competition, one-round disclosure and two-round disclosure—only **25 distinct record IDs were ever returned**. The union excludes discarded response candidates, the invalid competition attempt and oracle inputs. Oracle buyers did receive their entire designated catalogs.

| Partition of the frozen catalog | Records | Share |
|---|---:|---:|
| Ever returned in these five games, all within $800 | 25 | 5.4% |
| Never returned, listed price at or below $800 | 383 | 82.4% |
| Never returned, listed price above $800 | 57 | 12.3% |
| **Total** | **465** | **100%** |

Shares are rounded. A within-budget record is not necessarily a complete affordable setup: missing components can add costs, and prices remain unverified. Nevertheless, price alone excludes only 57 records. Of the 383 unreturned records within budget, **227 explicitly mention both grinding/bean-to-cup and milk/frothing/steam** in their title or available image-alt text. These are textual relevance signals, not verified functionality or suitability.

[Reproducible counts](summary.json) · [Record-by-record coverage and text flags](records.csv)

## 1. Repeated offers, but not 400 literal duplicates

Pagination produced **903 captured appearances**, already consolidated into 465 normalized records. Exact repeated normalized records were grouped during collection. The 465 records contain **455 exact titles**, or **448 titles** after removing case, accents, punctuation and spacing differences. Title normalization is only a diagnostic; truncated and generic names make it unsuitable as definitive product matching.

There are broader repeated model families across retailers, colors, versions, sponsorship and card formats. Examples identified by explicit text rules:

| Model-family label | Records | Frozen price range | Distinct records ever returned |
|---|---:|---:|---:|
| Breville Express Impress | 9 | $649.95–$649.99 | 3 |
| Breville Barista Touch, excluding Touch Impress | 9 | $969.00–$999.99 | 0 |
| Ninja Premier | 6 | $599.00–$599.99 | 5 |
| Magnifica Evo, excluding Evo Next | 6 | $737.00–$899.95 | 1 |
| Philips Baristina | 7 | $267.34–$499.95 | 0 |
| Ninja Mini, excluding Mini Plus | 2 | $449.99 | 1 |
| Chefman Crema Deluxe | 2 | $399.99–$499.99 | 0 |

These labels are **not verified identical SKUs**. A Baristina machine and milk-frother bundle, for example, can have materially different completeness. Repeated model names can still add meaningful seller, price or package choices. The competitive buyer's provider allocation actually depended on a small listing-clarity difference between similar Ninja offers.

The illustrative family rules label 87 records; the other 378 are simply outside those example rules, not 378 generic or inferior products. Many carry other brand names. Similar wording is insufficient evidence that differently branded machines share a manufacturer or quality. [Rules and complete family groups](family-examples.csv).

## 2. A large group of specification-led, lower-priced machines

The price distribution is heavily concentrated below $500:

| Listed price | Records |
|---|---:|
| Below $100 | 16 |
| $100 to below $300 | 166 |
| $300 to below $500 | 148 |
| $500 through $800 | 78 |
| Above $800 | 57 |

That is **330 records below $500**, many describing combinations of an espresso machine, grinder and milk frother. Across the full catalog, 216 title/image-text records mention 15- or 20-bar pressure. Numerous cards emphasize tank capacity, wattage, grind settings, steam wands and stainless-steel construction. They include brands such as Garvee, COWSAR, Kismile, VEVOR, EUHOMY, Gevi, AIRMSEN, Chefman and many others, as well as generic descriptions.

These records are often relevant to the functional brief. What they frequently do not establish is the information needed to distinguish expected ownership satisfaction: actual grind consistency, durability, preparation difficulty, support experience or seller-specific recourse. Repeating a pressure claim does not resolve those comparisons. The saved model explanations often lean on familiar model families, general package knowledge and reputation priors to fill those gaps.

This is an evidence limitation, not proof that cheaper or unfamiliar equipment is bad. The agents may be making useful simplifications, overlooking good alternatives, or expressing shared model biases; the current traces cannot determine the relative contribution of each.

## 3. Some offers add little for this particular buyer

A recognizable subset is unaffordable: premium Touch, Oracle, Rivelia and other offers exceed the ceiling. Other records describe brewing machines that need a separate grinder, or formats such as Nespresso that do not by themselves satisfy the whole-bean requirement. A cheap brewer is not a complete setup when no compatible grinder offer has been returned.

The search query, `espresso machine grinder milk frother`, predominantly produced machine and machine-bundle offers. It did not create a broad accessory catalog. This buyer wants one setup for two sequential morning drinks, has no color preference or brand loyalty, and does not value extra hardware merely because budget remains. Consequently, many products can be plausible substitutes while adding little as a second purchase.

That helps explain a one-machine basket. It does **not** establish that a one-to-ten-offer shortlist contains every meaningful substitute. Set descriptions can also conceal useful components; treating a whole bundle as one record is different from having separately priced component offers.

## 4. Evidence quality varies, including identifiable extraction problems

| Card characteristic | Count | Interpretation |
|---|---:|---|
| Title explicitly marked truncated | 99 | Model identity or features can be obscured; all 99 flags are in Bing records. Other descriptions can be incomplete without this flag. |
| Merchant explicitly marked aggregate | 56 | For example, “Walmart & more” does not uniquely identify an offer's seller or applicable terms. |
| Alibaba/Alibaba B2B merchant text | 38 | Household variant, quantities and offer terms may need interpretation; the label alone does not prove ineligibility. |
| Sponsored records | 148 | A source-placement attribute, not a quality or trust judgment. |
| Numeric-only merchant field | 2 | An identifiable extraction issue, described below. |

These categories overlap and must not be added together as a count of unusable records. Neither an unfamiliar merchant nor missing text automatically disqualifies a card under the current ordinary-shopping policy.

Two Google structured merchant fields contain **“1,500”** and **“1,000”** rather than merchant names. Their preserved card text and titles identify Crate & Barrel; the numbers appear alongside sale prices. One is the $1,199.95 Touch Impress, the other the $799.99 KitchenAid KF3. The full card text remains available to agents, but a structured-field interpretation could be distorted. This audit leaves the frozen records unchanged and records the issue rather than silently repairing the experiment's input. [Original example cards](example-cards.json).

## 5. Important alternatives were omitted

Three specific never-returned Google records illustrate why omission cannot stand in for worthlessness:

| Card | Frozen price / displayed merchant | Why it deserves attention | Remaining uncertainty |
|---|---|---|---|
| `google-c1ac723b3479e478c13f`: Ninja Mini with built-in grinder | $449.99 / Walmart & more | Same named family and price as Bing's winning Mini. It could matter to provider attribution and comparison. Google had this record in both rounds but never returned it. | Identical hardware/package and the actual seller are not established; the card does not enumerate every required function. |
| `google-ce916892b069dd413070`: Chefman Crema Deluxe, double boiler, conical burr grinder, steam wand | $399.99 / Best Buy & more | Explicit grinder/steam wording and a price $50 below the selected Mini make it a plausible alternative for assessment. | The displayed 3.2/5 rating comes from only four reviews; package, seller and actual performance remain uncertain. |
| `google-e330ec1bb31d6723d074`: AIRMSEN with burr grinder | $184.99 / Best Buy & more | A substantially cheaper named grinder-equipped machine, rather than an obviously unrelated search hit. | Milk steaming and full package suitability are not established by its short title/card. |

These are examples for further evaluation, not recommendations or proven superior products. Their unchanged source cards are in [example-cards.json](example-cards.json).

The decisive existing example is Bing's Mini itself: it was omitted in round 1 of the two-round game, then introduced after the buyer's follow-up and purchased. Its usefulness did not arise from a catalog or price change. **An offer can be strategically unreturned and later become the winning recommendation.** Google never saw Bing's new second-round reply, but it independently had its own Mini record available from the outset.

## Why lists stayed short

The recommendation output schemas do not impose a ten-item cap; one selected reply actually contained 11 records. The prompts require agents to compare several candidate responses, not to give a separate reason for excluding every catalog entry. In the two-round run, the buyer's own initial Bing message requested a small but varied set.

The traces support three explanations, with different evidentiary strength:

1. **Deliberate withholding, directly stated.** The sole recommenders explicitly omitted cheaper substitutes to preserve larger sales. In informed competition, Google considered a list containing the $429.99 Philips but preferred the list without it because the buyer might trade down.
2. **Selection of representative alternatives, visible in the actions.** Competitive lists often offered a lower-cost choice, guided-preparation choice and automation step-up. A small number of architectures may help compare this user's needs, while many other records occupy similar positions. That does not prove the selected representative is best.
3. **Incomplete model evaluation, plausible but not measured.** No exhaustive per-record utility scores, dominance proof or consistent eligibility classification was produced. The full catalogs were supplied to each recommender, but the public outputs mainly explain a handful of candidate lists. Those outputs do not establish whether every omitted record was carefully assessed, overlooked or discarded through a familiarity heuristic.

The warranted characterization is therefore: **a partly repetitive, unevenly described catalog with many affordable functional substitutes, filtered through strategic incentives and selective model judgment**. It is not a demonstrated 25-product frontier surrounded by 440 irrelevant offers. Establishing such a frontier would require a separate, explicit evaluation of coverage and omission quality.

## Method and reproducibility

This is an offline audit of unchanged cards and the selected public replies from five successful games. It does not rerun agents, browse products, alter scenario data, measure satisfaction or adjudicate merchant legitimacy.

[records.csv](records.csv) contains all 465 IDs, prices, returned-list coverage, example-family assignments and literal text flags. [summary.json](summary.json) contains aggregate counts. [family-examples.csv](family-examples.csv) exposes the actual IDs behind each illustrative group. [sources.json](sources.json) records source hashes and scope. All text flags use titles plus available image-alt text; absent words do not prove absent functions, and present words do not verify claims. Simple normalized-title counts do not perform fuzzy product deduplication.

Rebuild the audit from the repository root:

~~~bash
python3 -B reports/scenario-1-catalog-characterization/characterize.py
~~~

Read alongside the [strategic scenario comparison](../scenario-1-strategic-comparison/README.md). A useful next controlled test would hold the buyer input and recommender message fixed while adding selected omitted competitors, including Google's Mini. That would test whether omissions actually change purchases; this audit identifies the candidates without assuming the result.
