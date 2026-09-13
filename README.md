# Strategic recommendation games

Reproducible experiments in strategic interaction between buyer and recommender agents, using fixed recommendation datasets.

This repository currently contains **Scenario 1: Home espresso equipment**, with two frozen recommendation sets and fixed hidden buyer preferences. The first analysis examines a buyer with oracle access to every frozen recommendation.

The current [Scenario 1.3.0](scenarios/scenario-1/versions/1.3.0/README.md) excludes sponsored results and has an opt-in [frozen product-fact release](scenarios/scenario-1/product-facts/README.md).

| Recommendation set | Retained nonsponsored | Removed sponsored | Archived original |
|---|---:|---:|---:|
| Bing Shopping | **177** | 102 | 279 |
| Google Shopping | **140** | 46 | 186 |
| **Total** | **317** | **148** | **465** |

Every retained record has a product-fact file. There are page-supported facts for 205 records; 112 explicitly record missing usable detail or an unresolved identity/URL. Source provenance distinguishes merchant, manufacturer and affiliate product pages from shopping-provider specifications and indexed page copies.

Counts are distinct normalized **recommendation records**, not necessarily distinct products or merchants. Different offers, variants, prices, truncations or card descriptions remain separate. Page appearances and exact-repeat grouping are documented in the dataset files.

The collection query for both providers was `espresso machine grinder milk frother`. The search contained no budget or preferred product. The scenario includes the original $800 total equipment ceiling and the complete fixed preference profile in a buyer/evaluator-only file. “Hidden” describes information supplied to an agent during a future experiment: the preferences are intentionally visible to repository readers.

## Current buyer preferences

[Scenario 1.3.0](scenarios/scenario-1/versions/1.3.0/README.md) keeps the satisfaction-based Markdown preference brief from version 1.2.0, including the $800 equipment budget, seller trust and value for money. Its surviving cards and public context are unchanged. Versions 1.1.0 and 1.2.0 and all existing analysis traces retain their original 465-card inputs; old commands keep their meaning.

```bash
python3 tools/scenario_current.py validate
python3 tools/scenario_current.py context --role buyer
python3 tools/scenario_current.py records --provider google
python3 tools/scenario_current.py facts --provider google
```

The fact files are optional inputs for new analyses. Adding them does not rerun or retroactively revise any strategic scenario.

## Comparative report

[How strategic conditions changed recommendations and purchases](reports/scenario-1-strategic-comparison/README.md) compares oracle access, sole and competing recommenders, strategic disclosure and two communication rounds, with observed spending, agent choices, limitations and reproducible evidence tables.

[Catalog characterization](reports/scenario-1-catalog-characterization/README.md) examines all 465 cards, the 440 never returned in the validated strategic games, repeated families, price/evidence limitations and potentially consequential omissions.

## Analyses

- [Two rounds of strategic disclosure](analyses/scenario-1/two-round-strategic-disclosure/README.md): adaptive buyer follow-ups, selective sharing of rival offers, independent second replies, and a final choice from all four response lists.
- [Strategic buyer disclosure](analyses/scenario-1/strategic-disclosure/README.md): separately addressed buyer context, competing replies under partial information, and a final decision using the true preferences.
- [Competing recommenders, one shared buyer](analyses/scenario-1/competing-recommenders/README.md): independent informed Bing/Google responses, a buyer comparing both lists, and revenue attributed to purchased offers.
- [Informed recommender with a restricted buyer](analyses/scenario-1/informed-recommender/README.md): separate Bing/Google sequential games, full preference knowledge, strategic response selection, and buyer purchase decisions.
- [Oracle access to complete recommendations](analyses/scenario-1/oracle-access/README.md): game-theoretic reasoning, exact prompts, CLI/model run manifests, ranked choices, and reproduction commands.

The frozen Scenario 1 manifest remains a data-only snapshot. Analysis conditions and results are versioned separately under `analyses/`.

## Use the archived fixed data offline

Python 3.9+ is sufficient; there are no external dependencies or service calls.

```sh
python3 tools/scenario.py validate
python3 tools/scenario.py records --provider bing
python3 tools/scenario.py records --provider google
python3 tools/scenario.py context --role recommender
python3 tools/scenario.py context --role buyer
python3 -m unittest discover -s tests
```

Agent-facing briefs are Markdown. The context command prints those briefs as plain text; the Python loader returns their unchanged text in separate fields. The default context contains only public scenario information. Loading recommendation records is a separate action. The buyer context explicitly adds private preferences; it does not automatically receive either complete recommendation set. The loader is a convenience for constructing inputs, not a filesystem security boundary.

## Scenario files

```text
scenarios/scenario-1/
  scenario.json
  public_context.md
  private/user_preferences.md
  recommendations/bing.json
  recommendations/google.json
  README.md
  collection-method.md
  manifest.sha256
```

Each recommendation file contains a fixed record catalog, every captured occurrence, page/batch metadata and documented transformations. Records have stable IDs and content hashes. Whole-file hashes pin the scenario, including its hidden preferences.

Use these saved files to repeat work on the same recommendation universe. Repeating the live searches is a **new collection**: results, prices and sponsorship can change. Add any later analysis as a separate artifact referencing the scenario version and checksums; do not alter the frozen data to suit that analysis.

Raw browser dumps, screenshots, account details and tracking links are excluded. The cards are evidence of what the search interfaces displayed at collection time. The original cards remain unadjudicated. The separate product-fact release adds source-supported details with explicit limitations; it does not establish final checkout price, seller reliability or independently tested quality.
