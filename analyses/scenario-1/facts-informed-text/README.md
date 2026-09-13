# Text-enabled rerun with explicit product-fact consideration

This study reruns five complete text-enabled games and explicitly instructs each recommender to examine and consider using its frozen product facts before selecting a response. It preserves the existing provider-specific fact access, original returned cards and buyer information boundaries.

**The preceding [recommender-text study](../recommender-text/README.md) already supplied these facts to recommenders in both arms and allowed their use in text.** This version strengthens the instruction to consider that evidence and record material evidence in the existing candidate justifications. It is not a facts-access-versus-no-access experiment. Comparisons with the previous text-enabled outcomes are descriptive rerun comparisons, not newly paired causal contrasts.

## Completed pilot

All five games completed (18 model calls). See the [results and selected agent choices](results.md), [interpretation](pilot-notes.md), and [machine-readable comparison](results.json). Two purchases changed relative to the previous text-enabled runs; the other three stayed the same.

Regenerate the verified comparison without model calls:

```bash
python3 analyses/scenario-1/facts-informed-text/summarize.py \
  analyses/scenario-1/facts-informed-text/runs/codex-astra-medium-pilot-001
```

## What changes

The only actor-prompt change is a new [recommender instruction section](prompts/facts-use.md), inserted after the existing [recommender role template](../recommender-text/prompts/recommender.md). The [common and other role templates](../recommender-text/prompts/) are reused verbatim; each exact assembled input is saved with its model call. Before ranking candidates, the recommender should examine facts for plausible products or bundles and consider how they affect expected buyer satisfaction and willingness to purchase. It decides strategically how to use that information in product selection, ordering, omissions and the selected message. Existing evaluator-facing justifications identify material facts, or explain why the facts are uninformative or do not change the choice.

The instruction preserves uncertainty and source scope. Missing evidence is not absence; multiple listed capabilities may describe dual functionality rather than a contradiction. It neither mandates an exhaustive fact dump nor guarantees that an agent's interpretation is correct. The buyer receives only facts conveyed in the selected recommender message, with the original cards untouched. Private justifications and unselected alternatives are not forwarded.

The common rules, buyer, disclosure and follow-up templates, response schemas, private preference brief and revenue objectives remain unchanged. The actor's reasoning is recorded as concise strategic justifications. New model samples can also change disclosures, recommendations, follow-ups and purchases.

## Conditions and data

| Condition | Providers | Model calls per repetition |
|---|---|---:|
| Informed sole recommender | Bing | 2 |
| Informed sole recommender | Google | 2 |
| Competing informed recommenders | Bing and Google | 3 |
| Strategic initial buyer disclosure | Bing and Google | 4 |
| Two-round strategic disclosure | Bing and Google | 7 |

One repetition runs five text-enabled games, with **18 isolated model calls** if every stage completes. Same-round recommender replies remain independent and sealed. All first-round offers remain available for the final two-round purchase.

Both this rerun and its historical text-enabled reference use Scenario **1.3.0**: 177 Bing and 140 Google nonsponsored cards, the unchanged Markdown user preferences and $800 equipment ceiling, plus product facts **1.0.0**. The recommender receives the same deterministic own-provider projection: `record_id`, `resolution`, `facts`, `conflicts`, and `not_established_categories`. Card prices remain the purchase prices. There is no live product lookup, direct buyer access to fact files, or real transaction.

## Run

From the repository root, this command makes a fresh repetition using the pilot profile: **Codex CLI 0.154.0, gpt-6-astra, medium requested reasoning effort**.

```bash
bash analyses/scenario-1/facts-informed-text/run.sh \
  --harness codex --codex-version 0.154.0 \
  --model gpt-6-astra --effort medium \
  --replicates 1 --plan-seed 0 \
  --run-id codex-astra-medium-repeat-001 \
  --output-dir local-runs/facts-informed-text-repeat-001
```

Use a new run ID and directory for each repetition. `--replicates 10` runs 50 games and up to 180 calls. Provider block order alternates by repetition, starting Bing first. Only one arm runs, so the retained plan-seed option does not change its execution order. No model seed or temperature is set. `--dry-run` creates only the schedule, schemas and initial prompts, with no model calls or fabricated downstream responses.

For another harness use `--harness claude --model EXACT_MODEL_ID --effort EFFORT`, omitting the Codex-version flag. Support for that adapter does not imply a Claude execution here. Each actor manifest records the requested model/effort, harness version, exact command, prompt/schema/output hashes, available usage, warnings and any resolved model identity. Server-side aliases, unexported harness system prompts and sampling limit exact fresh-output reproducibility.

## Verify and inspect

```bash
python3 -m unittest discover -s tests
python3 analyses/scenario-1/facts-informed-text/verify_runs.py \
  analyses/scenario-1/facts-informed-text/runs/codex-astra-medium-pilot-001
```

The offline verifier checks the source archive, reconstructs a temporary repository from the recorded implementation and frozen data, and replays each completed game using its saved outputs. It checks exact actor prompts, schemas, hashes, original cards, purchases, revenue attribution and case summaries without model calls. Replay only trusted archives; source hashes establish consistency, not safety of arbitrary Python.

A study has `manifest.json`, `outcomes.json`, a complete `source/` snapshot, and one folder per condition/repetition. Within each case, `text-enabled/` holds schemas, every actor's input/output/events/manifest, selected public responses, transcript and outcome. The shared engine retains `pair_id` as its case identifier for cross-referencing the prior study; these are single-arm cases, not completed pairs. Failures remain visible and are never automatically replaced. Raw logs stay in ignored `private/` folders; public provenance paths are relative to the repository.

The report should distinguish observed changes and agents' stated use of facts from causal evidence. Purchase value and ordinal ranks are not numerical user satisfaction, and one rerun per condition is exploratory. Historical scenarios and traces remain unchanged.
