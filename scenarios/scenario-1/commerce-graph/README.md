# Frozen commerce evidence graph

[Release 1.0.0](versions/1.0.0/manifest.json) is a deterministic graph projection of Scenario **1.3.0** and product facts **1.0.0**. It connects the existing offers, source-supported claims, capabilities and evidence sources. No new product research, preferences, price changes or model calls are introduced.

The release contains **317 frozen offers, 1,608 product-fact claims, 52 separately scoped landing-page observations, 269 sources, 21 normalized capabilities and 4,834 relationships**. Of the offers, 205 have product-fact evidence and 112 retain explicit gaps. [Coverage report](versions/1.0.0/coverage.json).

## Files

```text
commerce-graph/
  README.md
  schema.json
  versions/1.0.0/
    manifest.json
    coverage.json
    schema.json                     # Frozen copy of the record schema
    build-source/commerce_graph.py  # Exact standalone builder/query implementation
    nodes/
      offers.jsonl
      products.jsonl
      sellers.jsonl
      claims.jsonl
      sources.jsonl
      capabilities.jsonl
    edges.jsonl
    mappings/
      identity-decisions.jsonl
      capability-mapping.json
      inference-rules.json
```

JSON Lines files contain one node or edge per line, sorted by stable ID. Claims retain the exact original fact object, evidence source IDs and locators. Sources reference the existing source files and hashes, including retrieval dates and representation types. The manifest pins all used card/fact/source files, mappings, schema and builder. Builds omit wall-clock metadata so replay can reproduce every release byte, including the manifest.

`products.jsonl` holds **offer-scoped product references**, not 317 established distinct physical products. This first release makes **zero identity merges**. Four pairs share resolved landing-page URLs and receive explicitly qualified candidate links. Shared titles, URLs, seller SKUs or source claims do not automatically establish that two frozen offers cover the same variant. No facts propagate through candidate identity links. A later reviewed identity policy should be a new graph version.

The 19 seller nodes are source-scoped seller-name references from landing-page observations. They are connected to those observations, **not to the original frozen offers as confirmed sellers**. A later observed price or availability never overwrites a frozen offer price. Merchant display labels and their aggregate flags remain attached to the original offer.

## Normalization and inference

The [capability mapping](versions/1.0.0/mappings/capability-mapping.json) uses exact typed values and explicit provider-specification strings. It preserves unmapped claims. For example, a provider's “Milk Frothing Pitcher” does not prove that a pitcher is included. A reported 120 V value is a voltage claim, not certification of every aspect of US compatibility. Pump, extraction and advertised pressure claims remain distinct; no broad numeric/unit equivalences are invented.

Every derived capability edge records its rule and supporting claim ID. Query status is one of `reported_true`, `reported_false`, `qualified`, `inconsistent`, or `unknown`. Missing facts are unknown. The Mini's manual and automatic milk claims retain their source qualifications; the graph does not declare those two capabilities inherently contradictory. Capability filtering excludes qualified evidence by default; callers can explicitly include qualified positive claims.

There are **no compatibility edges** in this release: the frozen evidence does not establish specific cross-product compatibility. A bundle query reports cost and supported capability coverage while marking compatibility and complete-setup suitability unestablished. It neither invents a standalone grinder offer nor concludes that two matching portafilter diameters prove compatibility.

The vocabulary is local and explicit. It is informed by the product/offer separation in [Schema.org Product](https://schema.org/Product) and [Offer](https://schema.org/Offer), and by evidence provenance concepts in [W3C PROV-O](https://www.w3.org/TR/prov-o/). The JSONL files are not claimed to be RDF, JSON-LD or a complete implementation of those ontologies.

## Build and verify

From the repository root, Python 3.9+ and the standard library are sufficient. No database, network access or external model service is needed.

```bash
python3 tools/commerce_graph.py validate

# Reproduce into a new directory; published releases are never overwritten.
python3 tools/commerce_graph.py build \
  --output local-runs/commerce-graph-rebuild \
  --mappings scenarios/scenario-1/commerce-graph/versions/1.0.0/mappings \
  --schema scenarios/scenario-1/commerce-graph/versions/1.0.0/schema.json

python3 -m unittest discover -s tests
```

Validation checks input/output checksums, then runs the archived builder and compares every release file byte for byte. Only replay trusted archives: source hashes establish consistency, not code safety. The archived builder can also be invoked directly with `--repo . build --output FRESH_DIRECTORY --mappings ... --schema ...` if the active builder has changed. The active builder's source hash is part of each newly built release.

## Query examples

```bash
# Evidence-backed capability candidates, ordered by frozen price then ID.
python3 tools/commerce_graph.py query --provider bing \
  --capability cap-integrated_grinder --capability cap-steam_wand_present \
  --max-price-cents 80000 --include-qualified --limit 10 --format table

# Full source-supported comparison of two explicitly selected Google offers.
python3 tools/commerce_graph.py query --provider google --operation compare \
  --record-id google-c1ac723b3479e478c13f \
  --record-id google-73d649a23e17eb409d3e --format graph

# Follow next_offset to enumerate later pages; no silently discarded results.
python3 tools/commerce_graph.py query --provider google --offset 20 --limit 20

# Buyer views require explicit visible IDs; there is no default buyer oracle.
python3 tools/commerce_graph.py query --role buyer \
  --allowed-id google-c1ac723b3479e478c13f \
  --operation inspect --record-id google-c1ac723b3479e478c13f
```

`find` filters and paginates; `inspect` retrieves scoped evidence; `compare` preserves all explicitly requested IDs; `bundle` totals unique frozen offers and reports capability coverage. Compare/bundle queries reject pagination that would silently drop requested components. Price filtering applies to `find`; `bundle` evaluates the combined price limit. Retrieval order is not a utility ranking. For a language-model integration, use targeted queries and explicit response budgets rather than injecting the whole graph.

Formats `facts-json`, `table` and `graph` expose equivalent evidence. The facts-JSON view includes the original fact structures **plus the shared normalization/identity annotations and source metadata**. It is not the exact earlier fact-only prompt payload. The table and graph forms share the same relationships and source claims; changing storage syntax alone is not expected to establish an advantage.

## Information boundaries

`GraphView(role='recommender', provider='bing')` fixes the allowable IDs when the view is constructed. Query methods cannot change that scope. Buyer views require explicit visible record IDs. A cross-provider candidate edge is omitted unless both endpoints are permitted and requested. Scoped source/product nodes contain no hidden reverse membership lists or rival offer counts. Global coverage and identity inventories are not attached to query responses.

Agent views exclude later offer observations and their seller nodes. Only an explicit researcher view may include them. No private preference brief is loaded. This is a query/input-construction boundary, **not filesystem isolation**: files are public research artifacts. A future tool-enabled agent harness must construct the scoped view itself, prevent actors from overriding it, and deny direct repository access. The existing frozen card loader remains the authority for returning unchanged recommendation cards.

See the [three-view access audit](../../../analyses/scenario-1/graph-access/README.md) for saved queries, responses and offline replay. No new recommendation outcomes are asserted by this graph release.
