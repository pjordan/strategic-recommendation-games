# Two rounds of strategic disclosure and competing recommendations

This extends [strategic disclosure](../strategic-disclosure/README.md) with an adaptive buyer follow-up and a second independent reply from each recommender. The buyer chooses only after observing **all four recommendation responses**. First-round offers remain available even if a provider omits them in its second reply.

**Published outcome:** the buyer revealed its budget and selectively shared rival cards in the follow-up. Bing added the $449.99 Ninja Mini; the buyer selected it from all 14 distinct returned offers. See the [complete choices and reasoning](outcomes.md).

The experiment uses unchanged [Scenario 1 version 1.2.0](../../../scenarios/scenario-1/versions/1.2.0/README.md): 279 frozen Bing records, 186 frozen Google records, and the fixed private satisfaction brief with an $800 equipment ceiling. These are simulated catalog representatives, not measurements of Bing's or Google's own policies. No live search, product verification, price negotiation or purchase occurs.

## Sequence and information

1. **Buyer initial disclosure.** With the full true private brief but no catalog, the buyer ranks at least three plans and chooses separately addressed initial messages. Both messages commit before either response arrives.
2. **Round-1 recommendations.** Each provider independently ranks at least three response candidates, including an empty list, and selects its own ordered records and accompanying message. It sees only public rules, its own catalog and its addressed buyer message. Both know a second round will follow.
3. **Buyer adaptive follow-up.** The buyer sees both public replies and its selected initial plan. It ranks at least three separately addressed follow-up plans and selects one. It may reveal more true preferences, request useful alternatives, accurately summarize a rival message, and selectively forward any observed first-round cards. Only the addressed message and explicitly forwarded cards reach each provider.
4. **Round-2 recommendations.** Each provider independently selects a second reply from at least three candidates. It sees its own prior selected strategy, belief and response, its original buyer message and its new addressed follow-up. It never receives the rival's full catalog, unshared response, buyer's other follow-up or simultaneous second reply. It may add previously omitted own records, repeat earlier records, or return an empty list. It cannot withdraw first-round offers or edit any price or record.
5. **Final buyer choice.** Using the full true preferences, its selected plans and all four public responses, the buyer ranks purchase outcomes and decline, then chooses a compatible bundle or declines. Products can come from either provider and either round. Never-returned records are unavailable.

Each stage is a fresh isolated model call: **seven calls for three logical agents**. Explicit selected prior state provides continuity; private alternative strategies are not transferred to opponents. At round 2, a recommender receives its own selected candidate, selection reason, buyer belief and public response, not its discarded candidate list. Buyer state similarly preserves selected plans/reasons and observed public history. This is a specified memory policy, not continuous hidden model memory.

The default presentation is round 1 then round 2, with Bing then Google inside each round. `--display-order google-first` reverses provider blocks consistently. Arrival speed never determines presentation order. Returned record ordering remains the recommender's choice.

## Objectives and action constraints

Let the buyer's true preference brief be θ. The buyer chooses separately addressed messages mᵖ₁, sees responses Rᴮ₁ and Rᴳ₁, chooses follow-ups mᵖ₂ with optional observed-card evidence Eᵖ₂, then sees Rᴮ₂ and Rᴳ₂. Its final feasible offer universe is:

**C = records(Rᴮ₁) ∪ records(Rᴳ₁) ∪ records(Rᴮ₂) ∪ records(Rᴳ₂).**

The buyer seeks the bundle S ⊆ C with greatest expected satisfaction under θ, subject to the true $800 total equipment budget, or the outside option of declining. Satisfaction includes fit, preparation effort, cleaning, reliability, seller trust and value for money. There are no supplied numerical preference weights. Agents express qualitative rankings and concise public justifications; these do not certify global optimization.

For provider p, realized payoff is **Σ price(i)** over purchased records i originating in p's catalog. Rival-only purchase or decline gives p zero. Mixed bundles split credit by purchased component origin. This is purchase revenue, the existing proxy for the recommender incentive; product margins, commissions and accounting profit are unavailable. Each provider anticipates the buyer and rival strategically under the information it actually receives.

Initial disclosures and follow-ups are **truthful but selective**. Withholding the exact budget or requesting a clearly nonbinding lower price range is allowed. Inventing needs, falsely stating the hard budget, fabricating competitor quotes, guaranteeing seller terms or committing the user to buy is not. Forwarded evidence is optional: the buyer returns `shared_record_ids` per recipient and the harness materializes those observed cards unchanged. The buyer may also accurately describe received text in its message. Forwarding does not transfer offer ownership.

Every first-round offer remains purchasable. Exact repeated IDs across rounds are deduplicated only for the final purchase universe and revenue, preserving first appearance. All original responses remain in the transcript. Different IDs remain distinct alternative offers, even when apparently describing the same model. Similarity does not justify buying duplicate equipment or crediting two providers for one purchased item.

In round 1, recommender forecasts concern the eventual purchase after adaptation; forecast IDs are limited to the current candidate list because future responses are unknown. In round 2, forecasts may select any own record already returned in round 1 or in the candidate second response. Thus an empty round-2 response can still predict own revenue. Forecast validation does not enforce the hidden true budget; actual purchase validation does.

## Prompts and reproduction

The exact templates are [initial buyer disclosure](prompts/disclosure.md), [adaptive buyer follow-up](prompts/followup.md), [recommender](prompts/recommender.md), and [final buyer decision](prompts/buyer.md). The runner injects the unchanged private **Markdown** brief only into buyer stages. It injects each catalog only into that provider's inputs; buyer-facing cards are materialized from selected IDs.

Each run saves every fully assembled `input.md`, structured `output.json`, public event projection, actor manifest, selected state, addressed messages/evidence, all four response lists, transcript and computed outcome. Source snapshots include the runner, verifier, schemas, templates, tests, configuration, shared model adapter and scenario loader. Ignored private harness logs are excluded from publication. No prompt relies on a local machine path or conversation context.

From the repository root, with an authenticated Codex CLI account and Node/npm available:

~~~bash
bash analyses/scenario-1/two-round-strategic-disclosure/run.sh \
  --harness codex --codex-version 0.154.0 \
  --model gpt-6-astra --effort medium \
  --display-order bing-first \
  --run-id two-round-repeat-001 \
  --output-dir local-runs/two-round-repeat-001
~~~

The pinned CLI version is recorded alongside the requested model and effort. Tools, plugins and memory are disabled through the existing isolated adapter; each call uses an empty temporary directory. For Codex, API-key overrides are removed so the run uses the signed-in subscription. Harness built-in system instructions and managed policies are not exported; they may vary across installations. No temperature or seed is set. Effective model/effort are left unknown where the harness does not report them. Reproduction preserves protocol, inputs and requested settings; it does not promise the same stochastic choices.

The shared adapter also accepts `--harness claude --model MODEL_ID --effort EFFORT`, omitting `--codex-version`, for an installed/authenticated Claude CLI. The local command records its version. No Claude run is implied by that support; compare manifests, not an invented model equivalence.

Use a new run ID and directory for every attempt. Existing directories are rejected. A failed attempt retains its trace and status rather than silently retrying or repairing model actions. `--dry-run` prepares the first buyer input without model calls; downstream inputs cannot exist until preceding choices are generated.

Replay a saved run offline, without model calls:

~~~bash
python3 -B analyses/scenario-1/two-round-strategic-disclosure/verify_runs.py
python3 -B -m unittest discover -s tests
~~~

For a local reproduction, pass its directory to the verifier. It checks exact assembled inputs and selected state, observed-card forwarding, original returned records, ID availability, cumulative offers, candidate/selection consistency, actual purchase totals, attribution and recorded hashes. These checks do not prove that persuasive prose is truthful, category assumptions are correct or a ranking is optimal; those require trace review or additional evidence.

## Interpretation

[Observed choices and outcome](outcomes.md) describe the published run. The extra round permits preference clarification, selective comparison of rival offers, new catalog selections and changed explanations. It cannot create a discount or erase an earlier offer.

A different final purchase than a previous one-round sample would not isolate the effect of another round: all actors know the horizon in advance, initial strategies can change, and model draws differ. Even a purchase of a newly revealed round-2 offer would establish its first availability on this path, not prove a causal satisfaction improvement. The buyer makes no binding or separately sampled purchase decision at the midpoint. Untested alternative message plans and candidate replies are forecasts, not observed counterfactuals. This is one sampled strategic path, not an equilibrium or optimal-policy proof.
