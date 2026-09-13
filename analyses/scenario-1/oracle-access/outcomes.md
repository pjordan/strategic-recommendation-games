# Observed oracle-access outcomes

All four successful runs used **Codex CLI 0.154.0, requested model `gpt-6-astra`, requested reasoning effort `medium`**, with a fresh context, the complete fixed provider record set, and no executed tools. One successful run was made for each treatment: Bing and Google separately under the original evidence policy, their combined universe under that policy, and the combined universe under the revised reasonable-representation policy. The exact resolved model snapshot and effective reasoning setting were not reported by the CLI; these fields remain null in the manifests.

| Provider | Evidence policy | Records supplied | Buyer selected outcome | Simulated purchase value / recommender payoff |
|---|---|---:|---|---:|
| Bing | Original card-evidence | 279 | Decline | $0 |
| Google | Original card-evidence | 186 | VEVOR, record `google-ceb6c802131f2c0a0c32` | $332.49 |
| Combined | Original card-evidence | 465 | Decline | $0 |
| Combined | Reasonable representation | 465 | AliExpress offer, record `bing-16f171fcd3e63a99145c` | $3.02 |

These are observed model choices, not verified buying advice, guaranteed global optima, or estimates of an engine's causal effect. The model ranked ten candidates in each single-provider run, eight in the original combined run, and seven in the revised combined run, always including decline. The full input contained every record; a claim in an answer that all records were reviewed is not independent proof of exhaustive reasoning.

## Bing: decline

The model identified low-cost integrated offers and stronger automatic-machine descriptions but found no sufficiently supported complete US-compatible setup. It provisionally accepted that an espresso-specific integrated grinder can suit its machine and that fully automatic operation can supply internal brewing/tamping equivalents. It remained uncertain about milk containers/connections and electrical configuration.

For example, it considered the $149.99 Yesurprise/Wayfair card and two $349.99 automatic-machine cards (COWSAR and VEVOR). The WHITE / US variant at $426.99 supported intended electrical compatibility but did not establish the other necessary equipment. It ranked decline first; unresolved purchases tied below it, while an explicit 220V offer and an over-budget offer were ranked lower. It did not reject a merchant or cheap price merely for being unfamiliar.

See [the exact Bing response](runs/codex-astra-medium-bing-002/output.json).

## Google: VEVOR at $332.49

The selected VEVOR card explicitly describes fully automatic espresso operation, a grinder with 15 levels, an automatic milk frother, and a removable milk reservoir. The model inferred internal brewing/tamping equivalents from automatic operation and treated the reservoir as evidence of the necessary milk vessel. It inferred US electrical suitability from the US shopping context, direct merchant listing, and delivery/return information; the card does not specify voltage or plug.

It ranked this purchase first and decline second. Cheaper offers remained unestablished in its assessment: the $91.16 Temu machine did not specify accessory coverage; the $98 EspressoWorks sets did not enumerate their pieces or identify the grinder; and the $317.99 Garvee card specified 120V but left operating accessories and the milk vessel unclear. It found no supported component combination that beat the selected integrated setup. Its candidate rankings and detailed reasons are in [the exact Google response](runs/codex-astra-medium-google-001/output.json).

## Combined: decline despite retaining the Google-selected offer

The combined run received all 279 Bing records followed by all 186 Google records, unchanged. Cross-provider component combinations were allowed. No product or offer deduplication was performed. The run completed with 120,049 reported input tokens and 1,741 output tokens; the reported reasoning-output count was 145. This measures one harness invocation, not a controlled estimate of computation needed by the task.

It ranked decline first. The same $332.49 VEVOR offer selected in the Google-only run was a leading rejected candidate: the model accepted its automatic brewing/tamping and milk-reservoir evidence but would not infer US electrical compatibility from retail context. It also considered the explicit-120V Garvee at $317.99 and the Bing WHITE / US variant at $426.99, judging their other completeness evidence insufficient. It found no supported cross-provider combination, and did not transfer specifications between different or merely similar products.

See the [exact combined response](runs/codex-astra-medium-combined-001/output.json), [full submitted prompt](runs/codex-astra-medium-combined-001/input.md), and [run manifest](runs/codex-astra-medium-combined-001/manifest.json). The combined condition has its own [prompt template](prompts/buyer-combined.md) and [configuration](combined-config.json); the original inputs and outputs are unchanged.

This is an important consistency limitation. If the eligibility judgments used in the Google-only run were held fixed, adding Bing alternatives could not make decline preferable while the qualifying VEVOR remained available. The combined run instead adopted a stricter electrical-evidence assumption. Thus the observed buyer policy is not a single stable eligibility function across these runs. That does not contradict the conditional game-theoretic argument, which explicitly holds the assessment rule fixed.

One sample per treatment cannot attribute this change to list length, Bing-first ordering, the extra duplicate-handling instructions, or random variation. The combined condition adds both offers and explicit permission to reason across providers. No counterbalanced-order or repeated-run experiment was performed.

## Revised reasonable-representation condition: buyer selects the $3.02 offer

The user then asked that recommendation results be assumed, to a reasonable degree, to represent the products they describe. Only the prompt's evidence paragraph was changed. The combined records, record order, prices, private preferences, output schema, requested model and effort, and pinned CLI version stayed fixed. The revised paragraph permits ordinary US-retail, product-category and standard-operating-accessory inferences while retaining explicit contradictions and material variant ambiguity as reasons for concern. No newly researched manufacturer facts were inserted into the input.

The buyer selected `bing-16f171fcd3e63a99145c`, whose title describes an espresso machine with a grinder and milk frother and whose frozen price is $3.02. It inferred US household compatibility from the consumer offer's US shopping context, interpreted the frother as the machine's milk-steaming system, and assumed the standard operating accessories or built-in equivalents were supplied. All of these material assumptions are disclosed in the [exact response](runs/codex-astra-medium-combined-reasonable-001/output.json).

| Rank | Candidate | Displayed equipment price | Model's assessment |
|---:|---|---:|---|
| 1 | AliExpress espresso/grinder/frother offer | $3.02 | Qualifies under the revised assumptions |
| 2 | Temu espresso/grinder/steam-wand offer | $91.16 | Qualifies |
| 3 | Kicctian/Walmart offer | $139.99 | Qualifies |
| 4 | Justsmart/Walmart offer | $146.99 | Qualifies |
| 5 | Yesurprise/Wayfair offer | $149.99 | Qualifies |
| 6 | Decline | $0 | Below qualifying purchases |
| 7 | Alibaba B2B offer | $29.50 | Household variant remains unestablished in the model's judgment |

Given qualification of the $3.02 offer, the minimum-cost conclusion is straightforward: it is the lowest-priced record in the complete universe, and every additional positively priced component increases cost. The recommender cannot hide that option from an ideal buyer with unrestricted oracle access, so the conditional simulated payoff is $3.02.

This is an assumption-dependent experimental result. The $3.02 number is a frozen, unverified search-card price; the run does not establish that a complete physical espresso setup could actually be purchased for that amount. The revised policy removes the prior documentation barrier and makes the outcome sensitive to an unusually low captured price. No price correction, anomaly filter, merchant whitelist or forced product selection was introduced after seeing the answer.

One run per evidence condition does not estimate the frequency or causal size of the prompt effect; stochastic variation remains possible. The buyer's explicit explanation nevertheless shows that it used the newly permitted compatibility and completeness assumptions. The [full input](runs/codex-astra-medium-combined-reasonable-001/input.md), [manifest](runs/codex-astra-medium-combined-reasonable-001/manifest.json), and [revised prompt](prompts/buyer-combined-reasonable.md) are preserved. Revised single-provider runs have not been made.

## What this says about strategy

For an ideal buyer applying a fixed assessment rule to the entire set, hiding or reordering offers cannot improve the recommender's payoff. The buyer selects its own best qualifying setup or declines. The recommender's incentive to seek higher spend remains, but its ability to restrict the buyer's choices is absent under this condition. All four actual responses gave this conditional reasoning.

The runs also show that **complete access does not eliminate ambiguity in suitability assessment**. The Google run accepted a contextual US-compatibility inference that the Bing run did not generally accept. This difference may reflect evidence differences and variable judgment in a single stochastic run. It prevents a clean claim that Google caused a purchase while Bing caused abstention. If the Google run required explicit voltage confirmation, its own stated limitation says it would decline.

A comparison across harnesses should therefore record both the selected products and the material inference policy. More repeated runs with the same provider/input are needed to estimate stability. Testing empirical resistance to recommender framing would additionally require controlled response-message interventions; that was not run here.

## Run provenance and failures

- `codex-astra-medium-bing-001`: installed CLI 0.147.0; server rejected Astra because a newer CLI was required. No buyer outcome.
- `codex-astra-medium-bing-002`: CLI 0.154.0; completed model turn; declined.
- `codex-astra-medium-google-001`: CLI 0.154.0; completed model turn; selected $332.49.
- `codex-astra-medium-combined-001`: CLI 0.154.0; completed model turn; declined; original exporter succeeded.
- `codex-astra-medium-combined-reasonable-001`: CLI 0.154.0; revised evidence policy; completed model turn; selected $3.02.
- Claude Code adapter: command construction tested without a model call against CLI 2.1.226. No Claude result is claimed.

The original exporter mistakenly rejected an `error`-typed warning that Code Mode was disabled by the experiment's own tool restrictions. The two original single-provider 0.154.0 model turns had completed successfully, and their only other item type was the final agent message. `recover_export.py` recovered the exact final message text from private raw CLI events without rerunning the models or editing their answers. The original runner source, warning, export failure and postprocessor checksum are retained in each manifest. The current runner accepts such nonfatal warnings only when the model turn completes and no tool item occurs.

The built-in harness system prompt is not reconstructed. Prompt templates, exact submitted inputs, schema, requested model/effort, CLI version, archived runner source, final output, public events, token usage and timestamps are preserved. Sampling seed and temperature were not set. The separate strict analyst-policy baseline was not supplied to either model.
