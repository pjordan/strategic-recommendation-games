# Scenario 1: buyer has oracle access to every recommendation

The buyer can inspect and choose from the complete fixed recommendation set, independently of the recommender's query, shortlist, or ordering. This removes the recommender's control over which offers are accessible. It does not make incomplete product-card claims into verified specifications.

Bing and Google are separate games. The buyer sees 279 Bing records or 186 Google records, plus the same Markdown user brief. Oracle lookup and deliberation are costless. The recommender seeks the total displayed purchase value, with zero for decline. It receives credit for any simulated purchase from the selected provider, including an offer absent from its own response. Prices and available records cannot change. These assumptions are fixed in `config.json`.

## Observed results

Codex CLI 0.154.0 with requested `gpt-6-astra` / `medium` declined on Bing and selected the $332.49 VEVOR offer on Google. The Google decision relies on a stated US-compatibility inference. Read [the outcome analysis and limitations](outcomes.md) before treating these as a comparison.

## What the game implies

Let D be one provider's entire record set, theta the buyer's private preferences, and F(D, theta, E) the setups that satisfy those preferences under the buyer's evidence assessment E. Setups can be integrated products or compatible combinations; total equipment price is the sum of the selected records' displayed prices. The outside option is decline.

The buyer chooses its most preferred outcome from F(D, theta, E) together with decline. If F is nonempty, the scenario preferences select the lowest-cost qualifying setup, using the stated tie-breaks at equal cost. If F is empty, the buyer declines.

A recommender action a may change its displayed subset, order, and prose. Under oracle access, it does not change D, theta, E, or prices. Consequently, the buyer's choice and the recommender's payoff are invariant to a. The recommender cannot increase revenue by hiding cheaper qualifying offers or putting expensive ones first. Any permitted response is a payoff-tied best response against that ideal buyer policy; returning the full set is a convenient representative, not a uniquely optimal strategy. The buyer need not disclose its budget to obtain this result.

This is a conditional optimal-choice argument. It assumes the buyer evaluates the complete set consistently and does not treat unsupported persuasive text as additional reliable evidence. It does not claim that finite-context language models are invariant to framing, that suitability judgments are objectively correct, or that we have solved a Bayesian equilibrium over unspecified buyer types. If access has a cost, purchasing is limited to the recommender's shortlist, new product evidence is allowed, or prices can change, the result need not hold.

## What is actually run

Each recorded model run is one fresh **buyer decision under full access**, with a compact ranked candidate set and a public explanation of the strategic consequences. It is not a two-agent conversation or an empirical test of every possible recommender message. The independent model receives no previous conversation, analyst-selected product, conservative assessment ledger, or expected answer.

The same task prompt, private brief, public brief, schema, and source records are used across harnesses for a given provider. Native harness system prompts and reasoning controls are not identical across products, so the unit of comparison is the **harness + exact version + requested/resolved model + reasoning setting + prompt/input hashes + tool policy** combination. Equal labels such as “medium” do not imply equal computation across harnesses. Do not label an unreported resolved snapshot as known.

- Task prompt: [`prompts/buyer.md`](prompts/buyer.md).
- Output contract: [`output-schema.json`](output-schema.json).
- Exact full prompt submitted in each run: `runs/<run-id>/input.md`.
- Settings, versions, hashes, timing, usage and execution status: `runs/<run-id>/manifest.json`.
- Actual final model response: `runs/<run-id>/output.json`.
- Public event projection: `runs/<run-id>/events.jsonl`.

The input includes each frozen record unchanged as a JSON object. It does not include repeated page occurrences: those are provenance, not new offers. The source files remain intact. Record IDs and prices in outputs are checked against the source, and the chosen outcome must be among the highest-ranked reported candidates. These checks do not independently certify product suitability or prove the model exhaustively considered every combination.

## Run a fresh assessment

Run these commands from the repository root using Python 3.9+, Bash, Node/npm for the pinned Codex package, and an authenticated CLI. The wrapper uses `npx` to run the specified Codex version. The Codex adapter uses the existing ChatGPT login. The initial installed-CLI attempt (0.147.0) was rejected because Astra required a newer version; it is retained as a failed run, not an outcome. No API key is stored in this repository. Output directories must be new; previous runs are never overwritten.

```bash
bash analyses/scenario-1/oracle-access/run.sh \
  --harness codex --codex-version 0.154.0 --model gpt-6-astra --effort medium \
  --provider bing --run-id codex-astra-medium-bing-repeat-001 \
  --output-dir local-runs/codex-astra-medium-bing-repeat-001

bash analyses/scenario-1/oracle-access/run.sh \
  --harness codex --codex-version 0.154.0 --model gpt-6-astra --effort medium \
  --provider google --run-id codex-astra-medium-google-repeat-001 \
  --output-dir local-runs/codex-astra-medium-google-repeat-001
```

The wrapper invokes `codex exec` with explicit model and reasoning effort, structured output, JSON events, a fresh empty working directory, ignored user configuration, and disabled tools/plugins/memory where supported. It supplies the complete prompt on stdin. The public manifest records argv with symbolic file paths. [Codex non-interactive documentation](https://learn.chatgpt.com/docs/non-interactive-mode) describes stdin prompts, event output and structured responses; [CLI options](https://learn.chatgpt.com/docs/developer-commands?surface=cli) document configuration isolation.

A Claude Code adapter accepts an explicitly chosen model identifier rather than guessing what “Claude 5.1” means. Its live execution is untested in this release. Its command options were checked against installed Claude Code 2.1.226. Supply a model your account supports:

```bash
read -r -p 'Exact Claude model identifier: ' analysis_model
bash analyses/scenario-1/oracle-access/run.sh \
  --harness claude --model "$analysis_model" --effort medium \
  --provider bing --run-id claude-medium-bing-001 \
  --output-dir local-runs/claude-medium-bing-001
```

Add `--dry-run` to prepare the exact input and command manifest without calling a model. The adapter uses safe mode, an empty tool set, no session persistence, and an empty temporary working directory. Managed harness policies and server-side model updates can still differ. A fresh stochastic model run may choose differently even with the same inputs; exact byte-for-byte reproduction refers to saved input and output verification, not guaranteed resampling.

## Separate conservative policy baseline

Before the independent model runs, a conservative analyst policy required explicit card support for every necessary attribute and made no standard-accessory or US-listing assumptions. It qualified no setup and selected decline in both datasets, giving the recommender zero. This is a transparent **conditional baseline**, not an observed model result or the unique outcome implied by oracle access.

Bing has 245 records priced at or below $800 and 34 above it; Google has 163 and 23. Low price alone does not establish a complete setup. Examples worth assessing include Bing's $3.02 AliExpress offer, Google's $91.16 Temu offer, and two $98 EspressoWorks sets. A “7-piece” or “10-piece” name does not enumerate contents in the saved evidence. Different credibility assumptions can change which setup qualifies.

The baseline ledger, reasoning, deterministic results and analytical response traces live under `policy-baseline/`. Its four response candidates return all cards in source order, all cards by descending price, only the highest-priced within-budget card, or no cards. Every action yields the same conditional decline outcome; the traces are labeled as analytical replays, not observed agent actions.

```bash
python3 -B analyses/scenario-1/oracle-access/policy-baseline/replay.py
```

This command verifies published judgments and recomputes their consequences. It makes no model call. The ledger is not used as input to the fresh model commands above.

## Verify saved model runs without calling a model

```bash
python3 -B analyses/scenario-1/oracle-access/verify_runs.py
python3 -B -m unittest discover -s tests
```

Verification checks exact input, archived runner source, schema, output/event hashes, product IDs, price arithmetic, and consistency between the reported ranking and selected action. Raw diagnostic logs under each run's `private/` directory are excluded from Git. New local experiments default to the ignored `local-runs/` directory in the commands above. Inspect any new output before publishing it; the runner screens exported responses for local paths and credential patterns.

Only the final public explanation and a filtered event trace are exported. The exact built-in harness prompt, server-side model snapshot when unreported, private internal reasoning, and credentials are not reconstructed. Repository readers can compare observed outcomes and rerun the documented setup, but should not mistake an alias or a reasoning-effort label for a complete specification of the service's internals.
