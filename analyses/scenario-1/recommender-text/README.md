# Paired whole-game study: recommender text

This analysis reruns complete strategic games with recommender commentary **enabled** and **disabled**. Agents know which communication channel is available and can adapt their choices. Both arms start fresh: historical buyer decisions are not reused as controls, and product lists are not held fixed.

The initial pilot is complete: [results and all choices](results.md), [interpretation of the changed outcome](pilot-notes.md), and [machine-readable comparisons](runs/codex-astra-medium-pilot-001/comparisons.json). All five pairs and 36 actor calls completed.

## What is paired

Each pair holds fixed the scenario and fact releases, strategic condition, provider identities, provider display order, replicate number, role instructions other than the communication policy, and harness/model/effort. All agents receive only their own arm's information. Sampling is independent; no shared model seed or temperature is available. A planning seed sets a near-balanced, shuffled order of arm execution. Provider display order alternates across replicates and is identical within each pair.

| Condition | Recommender knowledge | Buyer communication | Calls per pair |
|---|---|---|---:|
| Sole Bing | Full user preferences | Fixed initial request | 4 |
| Sole Google | Full user preferences | Fixed initial request | 4 |
| Competing Bing and Google | Full user preferences | Fixed initial request; buyer compares both lists | 6 |
| Strategic disclosure | Only addressed buyer context | Buyer selects initial messages | 8 |
| Two-round disclosure | Addressed context, then own prior state and addressed follow-up | Buyer selects initial messages and adaptive follow-ups | 14 |

One replicate runs five pairs, ten complete games and **36 isolated model calls** if all stages complete. Calls to recommenders in the same round run concurrently and are sealed until both finish. Two-round games preserve every first-round offer for final purchase, even if the second list omits it.

## Treatment and information boundaries

In `text-enabled`, the recommender selects an ordered subset of its own cards and an accompanying message. In `list-only`, its output schema has no message field; the public reply contains only provider identity and unchanged ordered cards, with round labels in the transcript. It can still select, omit and order products strategically. Internal forecasts, beliefs, ranking justifications and unselected candidates are recorded for evaluation but never forwarded as public commentary. Different private rationales do not make identical ordered lists distinct candidates in the list-only arm.

In multi-provider games, both recommenders switch policy together. This measures market-wide text availability, not the marginal contribution of Bing's or Google's text while holding its rival fixed. Product-card titles and descriptions remain unchanged in both arms; list-only does not remove marketing language already present in a frozen card.

Buyer-to-recommender messages remain available in both arms. A list-only buyer can discuss and forward observed cards, but receives no recommender prose to quote, summarize or carry into its follow-up state. Second-round recommenders see only their own selected prior state and the addressed buyer follow-up. The final buyer sees true preferences, its selected prior plans and every public reply from its own arm; no recommender private state or omitted catalog is supplied.

Both arms use **Scenario 1.3.0**, with 177 Bing and 140 Google nonsponsored records, and **product facts 1.0.0**. Each recommender receives its own cards and a deterministic projection of its own fact files: record ID, resolution metadata, claims with evidence locators, conflicts and unestablished categories. Retrieval attempts, offer observations and repeated file-level boilerplate are excluded. Shared instructions explain that claims are fallible and missing evidence is unknown. Prices always come from frozen cards. Buyers do not get fact files directly; the text arm can convey selected facts through prose. Consequently this study measures the value of the text channel for information as well as persuasion, not persuasion alone.

The two arms share new [Markdown role templates](prompts/) and a standardized recommender forecast contract adapted from the existing two-round analysis. The private buyer preference brief remains unchanged. Earlier analyses keep their original data, prompts and results. Comparisons to those historical outcomes involve additional changes and are not the paired text treatment.

## Formal interpretation

For condition `c`, replicate `i`, and policy `z` in {text-enabled, list-only}, let `Y(c,i,z)` be the outcome of a fresh complete game under `z`. The observed paired contrast is `Y(c,i,text-enabled) - Y(c,i,list-only)` for numeric outcomes. Treatment can change buyer disclosure, recommendations, follow-ups and final selection. This is the **total effect of allowing recommender text**, not a direct effect conditional on identical lists and not an established equilibrium response.

The report records purchase/decline, purchased IDs, item count, displayed spending, provider-attributed revenue, unique returned count, whether ordered lists or purchases changed, and the buyer's qualitative reasons. Higher spending is not automatically greater user satisfaction. Candidate ranks within separately generated sets are not comparable cardinal utility scores. There is no invented numerical satisfaction measure.

One pair per condition is a descriptive pilot. Independent model sampling can change outcomes even without treatment; a single changed choice does not establish causality. More replicates and counterbalanced provider order support stronger assessment. Trials with a failed arm remain visible as incomplete pairs and are excluded from completed-pair contrasts, with no automatic retry or favorable sample substitution.

## Run and reproduce

From the repository root, the initial pilot uses Codex CLI **0.154.0**, model **gpt-6-astra**, requested reasoning effort **medium**. Model resolution, usage, harness warnings and process commands are recorded per actor; server-side aliases and unexported harness system prompts limit exact fresh-sample reproducibility.

```bash
bash analyses/scenario-1/recommender-text/run.sh \
  --harness codex --codex-version 0.154.0 \
  --model gpt-6-astra --effort medium \
  --replicates 1 --plan-seed 0 \
  --run-id codex-astra-medium-repeat-001 \
  --output-dir local-runs/recommender-text-repeat-001
```

The command writes a fresh repetition outside the archived pilot. Use a fresh run ID and output directory for each study. `--replicates 10` schedules 50 pairs and up to 360 actor calls. `--dry-run` prepares the schedule, schemas and initial inputs without calling a model or fabricating downstream replies. For a Claude comparison use `--harness claude --model EXACT_MODEL_ID --effort EFFORT` without `--codex-version`; no Claude study is implied by adapter support.

```bash
python3 -m unittest discover -s tests
python3 analyses/scenario-1/recommender-text/verify_runs.py \
  analyses/scenario-1/recommender-text/runs/codex-astra-medium-pilot-001
```

The offline verifier checks the source archive, loads its recorded implementation in a temporary repository copy, validates frozen data and artifact hashes, reconstructs each completed game's exact prompts, validates schemas and purchases, and reconstructs paired comparisons without model calls. Replay only trusted source archives: matching hashes establish consistency, not safety of arbitrary Python.

## Artifacts

```text
runs/<study-id>/
  manifest.json                  # Fixed pair plan, profiles, data/source/artifact hashes
  comparisons.json               # One row per pair, including incomplete pairs
  source/                        # Exact implementation, schemas and prompt templates
  <condition-provider-replicate>/
    text-enabled/ or list-only/
      manifest.json              # Explicit arm status and failure, if any
      schemas/                   # Exact role schemas, including the treatment
      disclosure/                # If strategic initial messages are allowed
      round-1/<provider>/        # Each recommender's input, output, events, manifest
      followup/                  # If two-round communication is allowed
      round-2/<provider>/         # If two rounds
      buyer/                     # Final independent buyer decision
      responses.json
      transcript.json            # Selected public interaction only
      outcome.json
```

Per-actor raw logs stay in ignored `private/` directories. Public artifacts use repository-relative provenance paths. No actual purchase occurs.
