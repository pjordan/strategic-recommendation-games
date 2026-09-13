# Frozen product facts

[Release 1.0.0](versions/1.0.0/index.json) accompanies [Scenario 1.3.0](../versions/1.3.0/README.md), which removes all sponsored cards. Every surviving record has its own JSON file, keyed by its unchanged `record_id`. These are offer/listing identifiers, not a claim that every record is a distinct physical product.

## Coverage

| Evidence status | Bing | Google | Total |
|---|---:|---:|---:|
| Matched product landing page with extracted facts | 50 | 100 | 150 |
| Shopping-provider product-page specifications only | 55 | 0 | 55 |
| Page unavailable or no usable product detail retrieved | 60 | 12 | 72 |
| Candidate identity ambiguous | 6 | 13 | 19 |
| Product URL unresolved | 5 | 15 | 20 |
| Matched page without extractable specifications | 1 | 0 | 1 |
| **Files** | **177** | **140** | **317** |

**205 records have page-supported facts; 112 have an explicit unresolved/unavailable record rather than invented facts.** A file for every record does not mean every product was fully characterized. Even matched pages have missing categories. Merchant pages, manufacturer guides, and provider specifications are labeled separately in source provenance. Some merchant evidence comes from an indexed copy of the exact product URL when direct access failed.

The release contains 269 source representations. Multiple representations of one URL can have separate hashes. Collection occurred on September 13, 2026; original cards were collected September 12. `retrieved_at` is when the response was obtained, not a promise that a search index had crawled the page that day.

## Layout and meaning

```text
product-facts/
  README.md
  schema.json
  versions/1.0.0/
    manifest.json
    index.json
    products/<record-id>.json
    sources/<source-id>.json
    collection/resolution-plan.json
    collection/discovery-log.json
    collection/method.md
```

Each product file contains its original record hash, resolution status, typed factual claims with evidence locators, separate current offer observations, potential conflicts, unknown categories, and retrieval attempts. The [schema](schema.json) defines the format. Missing facts mean unknown, not absent. Boolean claims preserve explicit negative values, such as a specification stating that a machine has no integrated grinder.

These are **source-supported claims**, not physical testing or independent certification. Numeric pump ratings and extraction pressure can describe different things; differing units are not automatically classified as contradictions. Manual and automatic frothing claims can indicate either dual capability or conflicting copy. Retain that distinction when evaluating suitability.

Included accessories are recorded only when supported by scoped included-item text. Merely mentioning a milk pitcher or cleaning tool does not prove it is supplied. Product descriptions, structured specifications and explicitly scoped instructions are evidence; customer reviews, comparison products, shopping recommendations and surrounding ads are excluded from extraction.

`offer_observations` are current landing-page offers, often from structured page data. They may differ from the original seller, condition, variant or price. They never replace the frozen card's price. Seller reliability, shipping cost and return eligibility are not inferred from a storefront name. Missing seller/return terms remain unknown.

## Use in new analyses

```bash
python3 tools/scenario_current.py validate
python3 tools/scenario_current.py records --provider bing
python3 tools/scenario_current.py facts --provider google
python3 tools/scenario_current.py facts --record-id google-c1ac723b3479e478c13f
```

Pin both `scenario_version: 1.3.0` and `facts_version: 1.0.0`, plus their manifest hashes, in each new analysis. Recommenders can receive facts for their provider's records and cite the fact/source IDs in accompanying text. Recommendation card payloads remain untouched. The loader requires an explicit provider or record selection; it does not add facts or private preferences to the default recommender context.

A buyer receives only the facts the analysis condition permits. Giving a recommender the whole fact collection is not permission to give the buyer oracle access. Files are public research artifacts; loader roles are input-construction conventions, not filesystem security boundaries.

All existing analyses remain on their recorded versions and retain their original results. This release runs no new strategic game and makes no claim that past purchases would persist with these new inputs.

## Recollection and limitations

See [collection method and commands](versions/1.0.0/collection/method.md). Offline reproduction uses the frozen JSON and checksums and needs no network or external Python packages. Live recollection produces a **new** evidence snapshot; page availability, URLs and page text can change. The public release includes extraction code, URL-resolution decisions and locators, but excludes raw HTML, full search responses, cookies and browser dumps. Consequently, the raw-response hashes identify the private captures; they cannot be recomputed from the public factual summaries alone.
