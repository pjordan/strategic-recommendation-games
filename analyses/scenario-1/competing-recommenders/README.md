# Competing recommenders, one buyer observing every response

This extends the [informed-recommender analysis](../informed-recommender/README.md) into one shared game. The Bing and Google recommenders both know the full Scenario 1 version 1.2.0 user preferences. They independently commit their responses, then one buyer observes **both returned lists and messages before making a single purchase decision**.

The frozen catalogs, $800 total equipment budget, satisfaction-oriented Markdown preferences, ordinary purchasing judgment, and unmodifiable product records remain unchanged. The buyer has access to the union of the returned lists, not the full original catalogs. There is no live search or transaction. These are hypothetical agents over Google/Bing captures, not the companies' actual systems or policies.

## Initial observations

In the fully validated repeat, both recommenders returned three offers and led with a $599.99 Ninja Premier. The buyer ranked those offers equally, selecting Google's SharkNinja listing through a minor model-identification tie-break: Google received $599.99 and Bing $0. The earlier attempt selected Bing's $449.99 Mini but failed full-response validation on a mistyped ID in a lower-ranked alternative; it is preserved unchanged. [All observed choices and limitations](outcomes.md) report both attempts rather than treating the repeat as the only observed sample.

## Rules and information

| Participant | Information when acting | Permitted action | Objective |
|---|---|---|---|
| Bing recommender | All 279 Bing records, full user preferences, buyer instructions, game rules and knowledge that Google also submits | Ordered subset of Bing records plus message | Its own attributed purchase revenue |
| Google recommender | All 186 Google records, same preferences/instructions/rules and knowledge that Bing also submits | Ordered subset of Google records plus message | Its own attributed purchase revenue |
| Buyer | User preferences, rules, initial request, and both selected responses together | Any compatible subset of their union, including a cross-provider bundle, or decline | Expected purchase satisfaction within $800 |

Neither recommender sees the rival catalog or chosen response, receives buyer feedback, or revises after submission. Both know these information boundaries. Their independent submissions form a simultaneous move stage in the game, followed by the buyer's decision. The harness executes their model calls concurrently and constructs the buyer input only after both validated responses exist. No previous run, expected winner, or evaluator-only prediction is supplied to an actor.

The same fixed [initial user request](prompts/request.md) is used as in the preceding analysis. Strategic buyer queries, repeated negotiation, and live engine calls remain outside this condition. Disclosure of the normally hidden preference brief to both recommenders is an explicit analysis condition; the scenario itself is unchanged.

Each recommender ranks at least three distinct response candidates, including an empty list. It predicts whether the buyer will buy from itself, from the other provider, from both, or decline, and reports its own forecast purchased IDs/revenue only. These are qualitative forecasts under an unseen rival action, not calibrated probabilities or tested counterfactuals. The buyer never receives the unselected candidates or strategic forecast text.

## Purchase and revenue attribution

A response contains only the chosen message and exact frozen objects in the selected order. The script materializes IDs; the recommender cannot change any record field or return the rival's records. The buyer can ignore the suggested bundle and assemble another supported combination across lists. The budget applies once to all purchased equipment combined.

For purchased bundle B, provider i receives `R_i(B) = sum(price(r) for r in B if r originates in i's catalog)`. Decline pays both zero. A purchase entirely from Google pays Bing zero, and vice versa. A mixed bundle credits each provider only its purchased components. Total credited revenue must equal total purchase value.

This is purchase revenue, **not accounting profit**: product margins, commissions and costs are unavailable. Crediting both recommenders with the entire basket would reward the losing provider and would define a different game.

The same physical product may appear in both catalogs at the same or different prices. Preserve record IDs and offer details; do not award both providers credit merely because both listed it. Credit follows the exact offer record purchased. No fuzzy deduplication is performed, and similar titles do not establish identical products. The buyer is instructed to distinguish duplicate offers from extra hardware and not to buy redundant complete machines merely to increase spending. Physical identity and bundle usefulness remain judgments, not a complete machine-verified product ontology.

## Strategic implication

Previously, each recommender controlled the buyer's entire accessible list and faced only purchase versus decline when it returned one product. Here the rival's offers supply additional alternatives. A high-priced singleton can lose to a more satisfying competing offer even when it would have been acceptable by itself. Returning more useful alternatives can defend against a rival while inducing a lower-price choice inside the recommender's own list.

For responses `a_B` and `a_G`, the buyer selects its most preferred budget-feasible bundle from `S_B union S_G` and decline, under its evidence assessment. Each recommender seeks to maximize its own `R_i` under its beliefs about the rival response and buyer judgment. Prices are fixed: this is competition through offer selection and presentation, not price bidding or dynamic discounting.

A single observed response profile is not a Nash equilibrium or proof that either strategy is optimal. No complete numerical utility function, calibrated beliefs, exhaustive response search, or unilateral-deviation experiments are supplied. The changed recommender instructions and revenue attribution are part of the new condition; comparing it with previous samples does not isolate the causal effect of additional buyer visibility.

## Prompts and reproduction

- [Full recommender task template](prompts/recommender.md)
- [Full buyer task template](prompts/buyer.md)
- [Unchanged user preferences](../../../scenarios/scenario-1/versions/1.2.0/private/user_preferences.md)
- [Game configuration and pinned scenario hashes](config.json)
- [Recommender output schema](recommender-schema.json) and [buyer output schema](buyer-schema.json)

From the repository root, with Python 3.9+, Bash, Node/npm, and the authenticated Codex CLI subscription login:

```bash
bash analyses/scenario-1/competing-recommenders/run.sh \
  --harness codex --codex-version 0.154.0 \
  --model gpt-6-astra --effort medium \
  --display-order bing-first \
  --run-id competing-repeat-001 \
  --output-dir local-runs/competing-repeat-001
```

This runs three fresh model processes: two independent recommenders, then one buyer. All three use the specified harness/model/effort combination. `--display-order google-first` reverses the order of the provider blocks, retaining all records and each recommender's chosen internal ordering. The order is announced in the game instructions. It is not chosen from the outcomes. The initial sample uses Bing first; no counterbalanced result is implied.

Use a new run ID and output directory for every repetition. `--dry-run` prepares both recommender inputs and provenance without generating any response or fabricated buyer input. A Claude adapter is available through `--harness claude --model EXACT_MODEL_ID --effort EFFORT` without the Codex version flag; no Claude execution is claimed here. Existing harness limitations carry over: disabled tools/plugins/memory, fresh empty working directories, ignored user config/rules where supported, native unexported system prompts, unset seed/temperature, and potentially unresolved server-side model aliases. Identical inputs need not produce identical choices. Managed policies and effort settings are not necessarily equivalent across harnesses.

## Trace and verification

Each `runs/<run-id>/` contains:

- `manifest.json` and `source/`: scenario/source hashes, settings, order, status, timestamps and source snapshots.
- `recommenders/bing/` and `recommenders/google/`: each exact `input.md`, schema-shaped `output.json`, filtered events and role manifest.
- `responses.json`: both committed public responses, with all returned records intact.
- `buyer/`: the exact combined input, candidate ranking, selected outcome, filtered events and role manifest.
- `outcome.json`: the one purchase, revenue attributed to each provider, and each forecast compared with that decision.
- `transcript.json`: initial request, both public responses and the shared buyer decision. The two response blocks are presentation order, not evidence that the second recommender observed the first.

The structured response specifies which products were chosen; it does not insert a winning product or reusable canned answer. Private raw logs are ignored by Git. Public events contain final outputs and completion/usage events; private internal deliberation is not exported.

```bash
python3 -B analyses/scenario-1/competing-recommenders/verify_runs.py
python3 -B -m unittest discover -s tests
```

Pass local run directories as positional arguments to verify new repetitions. Checks reconstruct exact inputs; verify hashes, record integrity and ordering; ensure both responses reach the buyer; prohibit buying omitted products; check total budget and price arithmetic; and enforce that provider revenue sums to the one purchase total. These checks do not establish product truth, seller reliability, or exhaustive strategic reasoning. Previous scenario and analysis artifacts remain untouched.

[Observed choices and limitations](outcomes.md) distinguish recommender forecasts from the buyer's actual decision.
