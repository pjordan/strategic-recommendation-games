# Commerce graph access: equivalent-evidence audit

This first analysis establishes a reproducible access contract for the [frozen commerce graph](../../../scenarios/scenario-1/commerce-graph/README.md). It executes fixed, provider-scoped queries in three evidence representations: `facts-json`, `table`, and `graph`. **It is an offline access audit, not a new buyer/recommender game.** It makes zero model calls and produces no simulated purchases.

The [recorded audit](runs/access-audit-001/results.json) completed **27 queries**, covering every one of the 177 Bing and 140 Google offers through pagination. It verifies identical returned offer membership/order, capability status, relationships and underlying node evidence across representations. Additional examples inspect capability candidates and compare competing offers or candidate product identities. The fixed example queries—including their $800 price limit—are test fixtures, not an agent's hidden-preference inference or a prompt injected into an adaptive game.

## Reproduce

```bash
bash analyses/scenario-1/graph-access/run.sh \
  --run-id access-audit-repeat-001 \
  --output-dir local-runs/graph-access-audit-repeat-001

python3 analyses/scenario-1/graph-access/verify_runs.py \
  analyses/scenario-1/graph-access/runs/access-audit-001
```

Each run saves config, Python version, exact source snapshot, graph-manifest hash, every query request, its returned evidence and hashes, plus coverage and serialized response sizes. The recorded harness is `python-standard-library`, with `model: null` and `model_calls: 0`; it must not be compared to Codex/Astra purchase outcomes as though it were an LLM trial. Offline replay executes only trusted archived Python after verifying source hashes, then reconstructs queries and responses from the pinned graph.

The [config](config.json) defines all queries and representations. The [agent access contract](prompts/agent-access.md) describes how these views should be used when connected to a future experiment. The current runner does not expose a live tool to the existing game agents.

## What is held constant

All views use Scenario 1.3.0, facts 1.0.0 and graph 1.0.0. They receive the same own-provider offers, source claims, normalization results, uncertainty annotations and candidate identity relationships. Later landing-page prices and seller observations remain excluded. No buyer preference file is read. A provider-specific view excludes rival-only nodes and relationships, even when the public graph contains a potential cross-provider identity match.

`facts-json` preserves the original fact objects but supplements them with the annotations and provenance present in the other views. This makes the audit a comparison of representations with equivalent information. It is **not** identical to the older raw-facts condition; comparing against that historical condition would also change the available annotations and source metadata.

The serialized byte totals in `results.json` describe this fixed query workload, including repeated retrieval. They are not token counts or a measure of decision quality. The table representation is smaller than the graph representation in this audit. A graph is not automatically a more compact prompt.

## Next game experiment

The next agent-facing experiment should preserve the existing strategic conditions, frozen cards, facts, objectives and buyer information rules. It should add an explicit, bounded retrieval phase, use a trusted scoped `GraphView` for each role, record every tool request/response, and apply the same query, result-count and model-budget policies across conditions. Buyer output must still refer only to unchanged cards that recommenders actually returned.

Repeated runs could then compare candidate coverage, evidence errors, bundle completeness, purchased records, provider revenue and query/model cost. A normalized table with equivalent relationship access is an important control: any improvement over raw facts could otherwise reflect normalization or retrieval rather than graph structure. A separate raw-facts arm could measure that broader transformation, with its information differences documented explicitly. No claim of better recommendations, satisfaction or strategic performance is made by the present audit.
