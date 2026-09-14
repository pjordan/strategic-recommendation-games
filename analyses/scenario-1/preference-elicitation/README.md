# Preference elicitation before the final sales offer

Scenario 1, cards 1.3.0, facts 1.0.0. This two-round game extends the two-round case of [strategic-learning-text](../strategic-learning-text/README.md). Each recommender uses its initial selected text to ask 2–4 targeted questions, then uses the separately addressed buyer answer to tailor its final offer. Bing and Google agents maximize attributed purchase revenue (costs and margins are unavailable), while the buyer maximizes satisfaction under the unchanged $800 equipment budget.

The [completed pilot](results.md) selected Bing’s Ninja Premier at **$599.99**, compared with Google’s Ninja Mini at $449.99 in the prior two-round pilot. See the [interpretation and question audit](pilot-notes.md); the changed available set prevents treating this as an isolated preference reversal.

## Protocol

1. Buyer ranks truthful opening plans and sends a selected, separately addressed message to each provider.
2. Independent recommenders rank discovery responses, including a question-only empty list. They receive only their own catalog and frozen facts plus the addressed opening.
3. Buyer observes both selected replies, ranks answer plans, and sends separate truthful answers. It may withhold information or share actual rival offers. Preferences absent from the fixed brief remain unspecified.
4. Independent recommenders update their beliefs from their own answers and rank final responses. They cannot observe the rival's same-round reply.
5. Buyer selects a bundle or declines from the union of cards actually returned in all four selected replies. Earlier offers remain available.

Only selected messages and unchanged cards reach the other participant. Private candidate rankings, forecasts and concise decision rationales are saved for analysis. Frozen facts are available to recommenders, with explicit instructions to use them; the commerce graph is not an input. Existing strategic-learning instructions remain prompt heuristics, without a learned policy, measured regret or convergence guarantee.

A discovery response can forecast an eventual sale of an own-catalog product not yet returned. Its private round-1 forecast states a conditional answer and later offer, using the frozen price. This does not make that card visible or purchasable. Round-2 forecasts retain the previous restriction to that candidate plus the provider's actual earlier cards. Actual final purchases are always checked against the joint returned set and budget.

This is a combined protocol treatment: discovery/final-offer instructions, buyer opening/answer instructions and round-1 forecast semantics change together. Final buyer instructions, preferences, facts, cards and output schemas remain unchanged. Question counts and truthful interpretation are prompt requirements audited in the trace, not mechanically guaranteed by JSON validation.

## Reproduce

From the repository root, run a fresh game (seven model calls):

```bash
bash analyses/scenario-1/preference-elicitation/run.sh \
  --harness codex --codex-version 0.154.0 \
  --model gpt-6-astra --effort medium \
  --replicates 1 --plan-seed 0 \
  --run-id codex-astra-medium-pilot-001 \
  --output-dir analyses/scenario-1/preference-elicitation/runs/codex-astra-medium-pilot-001
```

Use a fresh run ID and output directory when the recorded pilot already exists. Add `--dry-run` to prepare initial inputs without model calls. Provider display order alternates across replicates; seed 0 does not seed the model. No model seed or temperature is set. The runner supports `--harness claude --model YOUR_MODEL --effort YOUR_EFFORT` without `--codex-version`, recording that installed harness profile for comparison. Authentication and availability depend on the participant's environment.

Verify the saved outputs offline with the archived implementation:

```bash
python3 analyses/scenario-1/preference-elicitation/verify_runs.py
python3 -m unittest discover -s tests
```

Exact expanded prompts are saved as each stage's `input.md`, along with structured outputs, event logs, schemas, manifests and source/data hashes. Prompt templates layer [common/role instructions](../recommender-text/prompts/), [facts use](../facts-informed-text/prompts/facts-use.md), [strategic learning](../strategic-learning-text/prompts/strategic-learning.md), and this condition's [opening](prompts/disclosure.md), [discovery](prompts/discovery.md), [answer](prompts/followup.md) and [final offer](prompts/final-offer.md). The final buyer role receives no additional instruction. The manifest records exact CLI version, requested model and effort, source commit, dirty state and any failure. No automatic retry or sample replacement occurs.

One game is a descriptive pilot. A historical comparison mixes protocol changes and model variation. Lower or higher spending alone does not establish satisfaction, causal benefit or an equilibrium. Offline replay verifies recorded inputs and decisions; it does not claim that a fresh model call will choose identically.
