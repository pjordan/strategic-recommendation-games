# Strategic recommendation games

Reproducible experiments in strategic interaction between buyer and recommender agents, using fixed recommendation datasets.

This repository currently contains **Scenario 1: Home espresso equipment**, with two frozen recommendation sets and fixed hidden buyer preferences. The first analysis examines a buyer with oracle access to every frozen recommendation.

| Recommendation set | Collection | Main records | Sponsored records | Total records |
|---|---|---:|---:|---:|
| Bing Shopping | Five numbered pages; main positions 1–177 | 177 | 102 | **279** |
| Google Shopping | Three cumulative batches; 60 → 100 → 140 main cards | 140 | 46 | **186** |

Counts are distinct normalized **recommendation records**, not necessarily distinct products or merchants. Different offers, variants, prices, truncations or card descriptions remain separate. Page appearances and exact-repeat grouping are documented in the dataset files.

The collection query for both providers was `espresso machine grinder milk frother`. The search contained no budget or preferred product. The scenario includes the original $800 total equipment ceiling and the complete fixed preference profile in a buyer/evaluator-only file. “Hidden” describes information supplied to an agent during a future experiment: the preferences are intentionally visible to repository readers.

## Analyses

- [Oracle access to complete recommendations](analyses/scenario-1/oracle-access/README.md): game-theoretic reasoning, exact prompts, CLI/model run manifests, ranked choices, and reproduction commands.

The frozen Scenario 1 manifest remains a data-only snapshot. Analysis conditions and results are versioned separately under `analyses/`.

## Use the fixed data offline

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

Raw browser dumps, screenshots, account details and tracking links are excluded. The cards are evidence of what the search interfaces displayed at collection time. Product completeness, seller condition, availability, final checkout price and quality have not been adjudicated in this dataset phase.
