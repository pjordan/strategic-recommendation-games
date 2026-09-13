# Observed outcomes: fully informed strategic recommenders

Each simulated recommender knew the complete Scenario 1 version 1.2.0 user preferences and its own frozen catalog. Each buyer could purchase only from the returned list. Both roles used **Codex CLI 0.154.0 / requested `gpt-6-astra` / requested reasoning effort `medium`**, with separate fresh processes, no executed tools, and no earlier results in their inputs. There was one successful game per provider.

| Simulated provider | Recommender's chosen response | Records returned / available | Buyer choice | Realized purchase value / recommender payoff |
|---|---|---:|---|---:|
| Bing | La Specialista Touch; Amazon.com displayed merchant | 1 / 279 | Purchase that product | $799.95 |
| Google | Magnifica Evo with automatic milk frother; Best Buy displayed merchant | 1 / 186 | Purchase that product | $749.99 |

The selected record IDs are `bing-8e7b383bc848c649b2a7` and `google-7eb494d8a25bff454d9e`. Both source cards were sponsored records, retained unchanged. The Bing card is truncated and does not identify the actual Amazon seller. Its buyer's acceptance should not be read as independent merchant or product validation. Google and Bing here label frozen catalogs, not actual company agents or policies. Payoffs measure purchase revenue; accounting profit cannot be calculated without margins and costs.

## Bing recommender's choices

The recommender ranked five complete response candidates. Each row below is its **forecast**, not a buyer observation for an unselected list.

| Recommender rank | Candidate response | Predicted purchase | Predicted revenue | Strategic assessment |
|---:|---|---|---:|---|
| 1, selected | Only La Specialista Touch / Amazon.com | Touch | $799.95 | Almost the entire budget, with beginner workflow assistance expected to justify acceptance; omit cheaper substitutes |
| 2 | Only Barista Express / Williams Sonoma | Express | $699.95 | Clearer retail identity supports acceptance; omit cheaper Express and Impress offers to preserve spend |
| 3 | Only Barista Express Impress / Williams Sonoma | Impress | $649.95 | Strong value and assisted preparation, but less revenue |
| 4 | Impress first, Ninja Premier / Best Buy second; message leans toward Ninja | Ninja | $599.99 | Credible alternatives may reassure the buyer, but likely cause a cheaper selection despite ordering |
| 5 | Empty list | Decline | $0 | No sale despite plausible available products |

It selected `touch_complete`, returned one record, and omitted 278. Its message emphasized assumed integrated grinding, guided preparation and assisted milk steaming, explained ongoing maintenance, and disclosed that normal US accessories and the actual seller/recourse were not verified. It explicitly said the price left only $0.05 below the equipment ceiling.

The buyer ranked purchasing the Touch first and declining second. It recognized the recommender's nearly budget-exhausting singleton strategy and distinguished Amazon's platform identity from the actual seller. Nevertheless, it judged the named product likely to supply a satisfying complete setup under normal package assumptions. It stated that acceptance over decline did not establish superiority over a cheaper omitted alternative. Its purchase matched the recommender's prediction.

The sparse card itself does not establish the grinder, guided preparation, assisted steaming, or accessory details. Both actors relied on stated model/package knowledge assumptions. Their agreement is not independent factual corroboration: both use the same requested model and share broad priors.

[Recommender candidates and exact chosen message](runs/codex-astra-medium-bing-002/recommender/output.json) · [Buyer decision and assumptions](runs/codex-astra-medium-bing-002/buyer/output.json) · [Untouched returned card](runs/codex-astra-medium-bing-002/response.json) · [Selected interaction](runs/codex-astra-medium-bing-002/transcript.json)

## Google recommender's choices

Again, the unselected rows report **recommender forecasts**, not tested buyer counterfactuals.

| Recommender rank | Candidate response | Predicted purchase | Predicted revenue | Strategic assessment |
|---:|---|---|---:|---|
| 1, selected | Only Magnifica Evo / Best Buy | Evo | $749.99 | Convenient complete milk-drink workflow and clearer merchant identity; omit cheaper substitutes |
| 2 | Only Barista Express Impress, Sea Salt / Williams-Sonoma | Impress | $649.95 | Strong acceptance prospect but lower revenue and more manual learning |
| 3 | Only Magnifica Start / Walmart - ElectroCell & more | Start | $769.00 | Slightly higher revenue, but extra seller uncertainty and no clear added benefit make acceptance risk less attractive |
| 4 | Impress first, Ninja Premier / SharkNinja second; message leans toward Ninja | Ninja | $599.99 | Likely cheaper switch; showing alternatives reduces expected revenue |
| 5 | Empty list | Decline | $0 | No sale |

The $769 candidate ranked below two lower-revenue candidates despite its predicted action being purchase: the recommender qualitatively discounted its acceptance confidence. No calibrated probability or numerical expected-revenue calculation was supplied. The ranking therefore reflects the model's risk judgment rather than a mechanically verified expected-profit optimum.

It selected `evo_complete`, returned one record, and omitted 185. The selected message justified $749.99 with automated whole-bean preparation and milk workflow, explicitly retained milk-system cleaning, and disclosed ordinary package and brand/retailer reputation assumptions. It did not claim specific warranty or return terms.

The buyer ranked purchasing the Evo first and declining second. It noticed the one-offer restriction and the recommender's high-spend incentive, and said it gave no independent evidentiary weight to the endorsement or budget framing. The actual named offer still appeared complete and convenient enough to justify buying. It noted that no cheaper alternative had been returned. Its purchase matched the recommender's prediction.

[Recommender candidates and exact chosen message](runs/codex-astra-medium-google-002/recommender/output.json) · [Buyer decision and assumptions](runs/codex-astra-medium-google-002/buyer/output.json) · [Untouched returned card](runs/codex-astra-medium-google-002/response.json) · [Selected interaction](runs/codex-astra-medium-google-002/transcript.json)

## What these observations support

Both recommenders independently selected a single expensive but plausibly acceptable product and explicitly reasoned that withholding cheaper substitutes could preserve revenue. Both buyers recognized the sales incentive while still preferring the available purchase to declining. The Google-side recommender also treated seller trust as relevant to acceptance: it forwent a $19.01 larger possible sale in favor of the apparently clearer offer.

This differs from full oracle access: the buyer can no longer select an omitted preferred bundle. However, these two games do not identify a causal revenue increase from omission, disclosure of preferences, or persuasive prose. Full-list responses and the other candidate lists were not actually tested, and the earlier oracle run had a combined catalog and different decision instructions. The observations demonstrate selected actions and successful acceptance forecasts, not an equilibrium, a globally optimal recommender strategy, or measured user welfare loss.

The top selected singleton offers leave no competing feasible bundle in the buyer's available set. Each buyer's observed choice is therefore a purchase-versus-decline comparison. No real purchase, live price check, product audit, or claim of actual Google/Bing behavior is made.

## Reproduction, provenance and failures

Run both games with:

```bash
bash analyses/scenario-1/informed-recommender/run-both.sh informed-repeat-001
```

The [analysis README](README.md#run-both-games) gives explicit harness/model flags, per-provider commands, prompts, artifact layout, and offline verification. Source snapshots, exact role inputs, output schemas, public events, timing and token usage are saved in each run. The resolved model snapshot and effective reasoning setting were not reported; temperature and seed were not set. Exact saved traces can be verified, but fresh samples need not select identical responses.

The `*-001` attempts failed before recommender generation because the service rejected `uniqueItems` in the output schema. They produced no agent choices or buyer turns. Their failed manifests, original inputs and source/schema snapshots are preserved, with a failure note. The `*-002` attempts removed that unsupported schema keyword while retaining local uniqueness validation; the agent prompts, catalog, preferences and game conditions stayed unchanged. Both complete games passed validation. No completed outcome was discarded or rerun to obtain a preferred result.
