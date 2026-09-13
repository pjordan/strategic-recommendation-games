# Collection method, release 1.0.0

## Inputs and execution

- Scenario: 1.3.0, 177 nonsponsored Bing and 140 nonsponsored Google records.
- Harness: Codex desktop with Python HTTP retrieval and the `web` search/open tool. No strategic buyer/recommender model run was performed.
- Extraction: deterministic Python rules and Beautiful Soup, with agent-reviewed URL/identity decisions. This is not an independent human audit.
- Runtime used: Python 3.9.6, Beautiful Soup 4.15.0. Collector source hashes are recorded in the release manifest.
- Agent model identifier and reasoning-effort setting were not captured by the collection scripts; they are therefore not asserted here. Model-game configurations in previous analysis manifests describe those games, not this collection.

## Process

1. Copy the previous scenario's preference brief unchanged. Filter records and appearances by the existing `sponsored` flag; retain surviving record bytes/IDs and relative order. This operational definition does not claim an independent advertising audit of each historical card.
2. Open each retained Bing `provider_product_url`, keyed by its product ID. Read the primary product title and product-specification table; resolve the selected merchant link. Alternative merchant cards are not used as substitutes for the listing. Bing grouping can itself be inconsistent; identity discrepancies remain unresolved.
3. Search each Google title within the displayed merchant's domain where identifiable. Preserve the discovery query, domain and timestamp. Examine candidates, reject categories/unrelated products, and retry obvious model/brand mismatches. No product URL was supplied by the original Google main-card capture.
4. Fetch proposed product pages using HTTP. Use web-tool page text where necessary, continuing long pages past navigation menus. When opening fails, search the product URL or title within the merchant domain and accept only a document matching that URL/product identifier on the same host. This fallback is labeled `indexed_product_document_text`.
5. Scope extraction to the primary JSON-LD Product description/attributes or the product's detail/specification sections. Exclude reviews, comparative products and recommendations. Preserve false specification values. Matching uses URL lineage, title agreement, model/variant checks and the explicit reviewed exceptions in the resolution plan. It is a documented matching judgment, not proof of immutable SKU identity.
6. Extract typed claims and attach a source ID and locator. Keep current offer data separate. Do not import a similar product's facts to fill a gap. Save one record even when the page or identity cannot be established.
7. Validate catalog membership, unchanged surviving payloads, source references, hashes, privacy screening, and consequential regression examples. Freeze the release and retain earlier scenarios/traces.

The [resolution plan](resolution-plan.json) contains proposed URLs, including candidates later rejected during page verification. **Its entries are not verified facts.** Use each product file's final `resolution` and `facts`. The [discovery log](discovery-log.json) records the original Google URL-discovery attempts without publishing search snippets.

## Reproduce the fixed inputs offline

From the repository root:

```bash
python3 tools/scenario_current.py validate
python3 -m unittest discover -s tests
mkdir -p local-runs
python3 tools/scenario_current.py facts --provider bing > local-runs/bing-facts.json
```

The exact frozen product JSON is the reusable experiment input. Existing analysis runners intentionally continue to load the archived catalog; a new fact-enabled analysis must explicitly use the current loader and pin both versions.

## Recollect live pages into a new snapshot

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-facts.txt
mkdir -p .cache/product-facts local-runs
bash scripts/collect_product_facts.sh .cache/product-facts local-runs/recollected-facts
```

This command repeats the HTTP stage using the saved resolution plan and builds a new local output. It does not reproduce the agent's interactive searches or web-tool page access, and will generally have lower coverage on sites requiring those fallbacks. HTTP failures remain explicit. The builder refuses to overwrite a directory containing a frozen manifest.

For comparable coverage, a web-enabled harness must also resolve currently ambiguous identities and open the same candidate URLs. Cache web-tool responses as `web-pages/<sha256(url)>.json` with `url`, `retrieved_at`, `method: "web.open"`, and `result` containing the tool's numbered page text. Concatenate page-range responses when navigation exceeds the first response. Exact-URL search fallbacks go in `indexed-pages/<sha256(url)>.json` with `url`, `retrieved_at`, and the search tool's plain-text `result`, then run:

```bash
python3 tools/product_facts_indexed.py --cache-dir .cache/product-facts
python3 tools/product_facts_build.py --cache-dir .cache/product-facts --output local-runs/recollected-with-web-facts
```

The text adapters target the web-tool representation used for this collection; other harnesses need an equivalent adapter. Reusing a cache reproduces those extraction inputs; refreshing it creates new observations. Compare new claims and matches before publishing a new version. Do not silently overwrite release 1.0.0 or reinterpret historical analysis outcomes.
