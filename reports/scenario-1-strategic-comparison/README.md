# How strategic conditions changed recommendations and purchases

**Scenario 1 comparative report · 13 September 2026**

Across the successful satisfaction-based runs, sole recommenders selected single offers near the buyer's $800 budget; competition prompted broader lists and a $599.99 purchase; buyer-controlled disclosure produced a $449.99 purchase. A second communication round changed how the winning offer was discovered but ended with the same product and price as the one-round disclosure run.

These differences came from **which frozen offers agents exposed and how the buyer assessed them**. No agent changed a price. The traces demonstrate strategic choices and responses, but the small number of samples does not establish causal effects, an optimal strategy, or improved user satisfaction merely because spending fell.

## Scope and common setup

The main comparison uses the same [Scenario 1 version 1.2.0 preference brief](../../scenarios/scenario-1/versions/1.2.0/private/user_preferences.md) and the same 465 frozen recommendation records: 279 Bing and 186 Google. Different records can describe alternative offers of similar equipment; 465 is not a count of unique products.

The synthetic buyer is a US beginner starting without equipment, seeking two sequential milk-based espresso drinks each morning from whole beans. The total equipment ceiling is $800 before tax and shipping. The buyer seeks expected satisfaction from drink quality, workflow, cleaning, dependability, seller trust and value for money. Saving money matters, but neither the cheapest purchase nor spending the full budget is the objective. Numerical utility weights are not supplied.

Strategic recommenders maximize the frozen purchase value attributed to their own purchased records. This is **revenue, not accounting profit**; margins and commissions are unavailable. They may omit or reorder records and add explanatory text, but cannot edit product cards, invent offers or negotiate discounts. Buyers may decline. In shared games, they may combine useful components across returned lists.

All six successful traces in the main comparison used **Codex CLI 0.154.0 / requested gpt-6-astra / requested medium**, with isolated role inputs and no executed tools. Effective model identity and effort were not reported; seed and temperature were unset. These are simulated agents using Bing and Google catalogs, not observations of the companies' actual recommendation policies. No new model run, live shopping research or purchase was performed for this report.

## Outcomes at a glance

Each row is a separate observed path. B1 and B2 are separate games, not two sales within one buyer's shopping session.

| Condition | Information and choice structure | Distinct records available to final buyer | Purchase | Spend | Budget left |
|---|---|---:|---|---:|---:|
| **A. Oracle access** | Buyer sees every frozen record; no strategic recommender call | 465 | Breville Express Impress / Williams-Sonoma | **$649.95** | $150.05 |
| **B1. Sole informed Bing** | Recommender knows full preferences; buyer sees only its chosen list | 1 | De'Longhi La Specialista Touch / Amazon.com | **$799.95** | $0.05 |
| **B2. Sole informed Google** | Same structure, using Google's catalog | 1 | De'Longhi Magnifica Evo / Best Buy | **$749.99** | $50.01 |
| **C. Competing informed recommenders** | Both know full preferences; buyer compares their independent replies | 6 | Ninja Premier / SharkNinja, through Google | **$599.99** | $200.01 |
| **D. Strategic disclosure, one round** | Buyer chooses separate initial messages; providers receive partial information | 19 | Ninja Mini / Target, through Bing | **$449.99** | $350.01 |
| **E. Strategic disclosure, two rounds** | Buyer adapts messages after both first replies; final choice retains all four lists | 14 | Same Ninja Mini / Target, through Bing | **$449.99** | $350.01 |

Sources: [A](../../analyses/scenario-1/oracle-access/runs/codex-astra-medium-combined-satisfaction-001/output.json), [B1](../../analyses/scenario-1/informed-recommender/runs/codex-astra-medium-bing-002/outcome.json), [B2](../../analyses/scenario-1/informed-recommender/runs/codex-astra-medium-google-002/outcome.json), [C](../../analyses/scenario-1/competing-recommenders/runs/codex-astra-medium-bing-first-002/outcome.json), [D](../../analyses/scenario-1/strategic-disclosure/runs/codex-astra-medium-bing-first-001/outcome.json), [E](../../analyses/scenario-1/two-round-strategic-disclosure/runs/codex-astra-medium-bing-first-001/outcome.json). The [generated comparison CSV](comparison.csv) includes exact record IDs, model-call counts and attribution.

The sole-recommender purchases were $150.00 and $100.04 above the oracle sample. The competitive purchase was $199.96 below the sole-Bing purchase and $150.00 below the sole-Google purchase. The disclosure purchase was another $150.00 below the competitive sample. These are arithmetic differences between observed runs, **not estimated treatment effects or welfare gains**.

## What changed strategically

### A. Complete access removed the ability to hide alternatives

The oracle buyer selected the $649.95 Express Impress, narrowly preferring its assumed preparation assistance and equipment/retailer confidence to the $599.99 Ninja Premier. It used all 465 cards as its available universe, although its output ranked only nine selected candidate outcomes. Oracle access here means access to cards, not perfect product knowledge or proof of exhaustive optimization.

For an ideal buyer with a fixed assessment rule and access to every offer, a recommender cannot remove a preferred option by omitting it from a message. That is a property of the defined information condition. This run did not separately test how persuasive framing might change the model's assessment.

The Mini later purchased for $449.99 was already in the frozen universe. Its absence from the oracle buyer's ranked shortlist is a reason to avoid calling the oracle result a verified satisfaction optimum. More access does not guarantee that a particular model sample will identify or evaluate every useful comparison. [Oracle reasoning and limitations](../../analyses/scenario-1/oracle-access/outcomes.md#current-satisfaction-condition-64995-barista-express-impress).

### B. A sole recommender used omission to preserve a larger sale

Both informed recommenders chose exactly one expensive, plausibly acceptable product and explicitly reasoned that cheaper alternatives could reduce revenue. Bing omitted 278 records; Google omitted 185. Each compared five response candidates before selecting its singleton.

Bing selected the $799.95 Touch, leaving five cents below the ceiling. Google selected the $749.99 Evo. Google considered a $769 Magnifica Start but ranked it lower because the extra potential revenue did not justify its perceived seller uncertainty. Its strategy accounted for acceptance risk rather than mechanically choosing the largest price.

Both buyers recognized the incentive and the restricted list, yet preferred the available purchase to declining. Neither claimed that the singleton was better than every omitted alternative. This is the central mechanism shown by these traces: **recognizing a seller's incentive does not restore missing choices**. Both recommenders' selected purchase forecasts matched. The unselected lists were not actually presented to buyers, so the causal contribution of omission versus framing remains unmeasured. [Candidate strategies and buyer explanations](../../analyses/scenario-1/informed-recommender/outcomes.md).

### C. Competition made broader lists attractive to the recommenders

When both informed recommenders competed for the same purchase, each selected a three-offer list. Their explanations emphasized the risk of losing to a rival's convenience or value proposition. Both led with a $599.99 Ninja Premier while preserving alternative workflows.

The buyer selected Google's Ninja. It ranked the two Ninja offers equally in expected satisfaction, then used Google's explicit model identification as a minor clarity tie-break. The buyer did not claim superior hardware or seller recourse. The resulting attribution—Google $599.99, Bing $0—therefore rested on a narrow listing judgment. Both agents predicted winning their own Ninja sale; only Google's prediction matched.

Competition did not eliminate strategic omission. Google explicitly considered adding a $429.99 Philips offer but selected the list without it, anticipating that the cheaper option could draw the purchase away from its Ninja. The observed strategy was to provide enough alternatives to compete while retaining a larger-sale opportunity. [Selected and rejected response candidates](../../analyses/scenario-1/competing-recommenders/outcomes.md).

An earlier attempt under the same rules selected Bing's $449.99 Mini. Its full buyer response was invalid because a lower-ranked alternative contained a mistyped record ID. That observed choice is retained, but excluded from the validated table. Resampling all three roles produced the $599.99 Google outcome. This variation directly limits any claim that condition C reliably yields that price or provider.

### D. Buyer-controlled disclosure changed the requests and the returned alternatives

The buyer ranked three disclosure plans and selected different messages: it revealed the exact $800 ceiling to Bing while giving Google a nonbinding $450–$650 exploration range and withholding the maximum. Both messages disclosed functional requirements and value criteria and requested useful alternatives. The buyer had not seen either catalog; it described the provider assignment as arbitrary.

Bing returned 11 offers and Google eight. Bing predicted a $649.95 Impress sale; Google predicted a $599.99 Ninja Premier sale. The buyer instead selected Bing's $449.99 Mini, judging its expected preparation assistance worth more than the savings from cheaper qualifying setups and the higher tiers insufficiently valuable.

Relative to C's validated sample, the visible set expanded from six to 19 records and the purchase fell by $150.00. However, **the winner came from the provider that knew the exact budget**. The run does not show that budget secrecy caused the outcome. The messages also changed emphasis and requested breadth, and the earlier invalid C attempt had already selected the Mini with fully informed recommenders. [Disclosure plans and observed choices](../../analyses/scenario-1/strategic-disclosure/outcomes.md).

### E. A second round made adaptation and selective rival comparison observable

The two-round buyer initially withheld the ceiling from both providers. It asked Bing to explore components around a nonbinding $600 target and Google to explore integrated workflows across tiers. Bing returned five offers and Google eight. Neither supplied a standalone grinder, leaving the proposed separate-machine route incomplete.

The buyer then selected a follow-up plan that revealed the actual $800 ceiling to both and shared different evidence:

- **To Bing:** Google's Chefman at $329.99, Philips Barista Brew at $429.99 and Magnifica Evo at $749.99, challenging both price and automation premiums.
- **To Google:** Bing's Ninja Premier at $599.99 and Impress at $649.95, inviting supported comparisons of similar offers and seller confidence.

The buyer asked for complete systems and useful previously omitted options. Bing added the $449.99 Mini, explicitly reasoning that it offered a better chance of retaining a sale against the cheaper rival systems, even if it displaced a larger own purchase. Google added no products and strengthened its Ninja-led explanation. It could not see Bing's simultaneous second reply or the newly added Mini.

The final buyer selected the Mini. Bing's round-2 forecast matched the exact purchase; Google's did not. The four replies contained 21 appearances of 14 distinct IDs, and all first-round offers remained available. The Mini was the only newly introduced round-2 record.

This is direct evidence of the **observed adaptive sequence**: the buyer shared competitive evidence, Bing reported responding to it by exposing another offer, and the buyer purchased that offer. It does not isolate the effect of sharing evidence from revealing the ceiling or clarifying preferences, because those happened together. The final purchase matches D, where the Mini appeared in the first reply. Another round changed the route, not the observed terminal purchase. [Full two-round analysis](../../analyses/scenario-1/two-round-strategic-disclosure/outcomes.md).

## Revenue, satisfaction and basket size are different outcomes

| Shared-game condition | Bing's realized revenue | Google's realized revenue | Purchase count |
|---|---:|---:|---:|
| C. Informed competition, validated repeat | $0 | $599.99 | One machine |
| D. One-round disclosure | $449.99 | $0 | One machine |
| E. Two-round disclosure | $449.99 | $0 | One machine |

All six main traces selected one machine. The lower spending in D and E does not mean the buyer simply minimized price: it rejected qualifying $329.99 and $429.99 alternatives in favor of the Mini's expected assistance. Conversely, the higher spending in B does not establish measured welfare loss: those buyers found their only available purchase preferable to declining. There is no stable numerical satisfaction measure connecting these separate model judgments.

The absence of additional items is partly a limitation of the opportunities presented. In E all 14 returned offers were machines, not complementary accessories or standalone grinders. The buyer assumed the selected integrated machine supplied required basics, and its prompt explicitly discouraged redundant machines or spending merely to exhaust the budget. The recommenders mainly tried to induce a more expensive replacement choice. These runs therefore provide little evidence about accessory cross-selling or expansion of a useful basket. Such a test would require complementary frozen offers and preferences that permit their incremental benefits to matter.

## Earlier evidence-policy experiments belong in a separate comparison

Before the satisfaction brief, the buyer used a cost-first preference ordering. Changing its evidence policy produced large differences even without strategic recommender calls:

| Earlier oracle condition | Observed decision |
|---|---|
| Original card-evidence policy, Bing only | Decline |
| Original card-evidence policy, Google only | VEVOR at $332.49 |
| Original card-evidence policy, combined | Decline, despite retaining the same VEVOR offer |
| More permissive representation policy, combined and cost-first | AliExpress headline offer at $3.02 |
| Revised satisfaction and ordinary-shopping policy, combined | Impress at $649.95; row A above |

The combined strict run used a different compatibility inference from the Google-only run. The $3.02 purchase depended on accepting an unverified headline price and standard-package assumptions under a cost-first objective. Neither result establishes real availability or legitimate checkout pricing. The later satisfaction revision changed both preference ordering and evidence interpretation. Those changes cannot be attributed to strategic competition and should not be folded into a single spending trend. [Original oracle traces and policy history](../../analyses/scenario-1/oracle-access/outcomes.md).

## Strength of evidence and next comparisons

The strongest evidence is the saved action sequence: selected messages, omitted and returned cards, ranked candidate responses, explicit forecasts and final purchases. The traces support the interpretation that omission, competition, information disclosure and adaptive comparison can matter through distinct mechanisms. They do not establish which policy is best in expectation.

There is one validated sample for each main table row. Unselected candidates are agent forecasts, not executed counterfactuals. No equilibrium, exhaustive unilateral-deviation analysis, counterbalanced-order result or cross-model comparison was obtained. Normal package and seller-reputation assumptions remain unverified and vary across model judgments. Agents sharing a model can share assumptions; agreement is not independent product validation.

The [complete attempt inventory](attempts.csv) covers 14 archived attempts: ten completed traces, including the four earlier cost-first outcomes, and four failed attempts. Three failures produced no buyer decision: one old-CLI incompatibility and two unsupported-schema rejections. The fourth is the competition attempt with a valid selected Mini ID but an invalid lower-ranked alternative. Earlier oracle exporter recovery preserved completed messages without rerunning them; the oracle analysis documents this provenance. Failed and recovered records remain available rather than being silently omitted.

The most useful next comparisons would hold more conditions fixed:

1. **Omission:** present the same buyer with a selected singleton, the same offer plus cheaper alternatives, and the full catalog; control accompanying prose.
2. **Disclosure:** repeat full-budget, hidden-budget and nonbinding-target messages with matched substantive requests and swapped provider assignments.
3. **Second-round information:** start from fixed first-round replies and compare preference clarification alone, rival evidence alone, both and no follow-up. Test announcing the horizon separately.
4. **Stability and welfare:** repeat and counterbalance provider order, report interface failures and outcome distributions, and use an explicitly specified common evaluation of satisfaction before making welfare claims.
5. **Basket expansion:** add a separately versioned catalog of useful complementary items and test whether revenue-seeking recommenders induce valued additions or redundant expenditure.

## Traceability and reproduction

[comparison.csv](comparison.csv) contains the six main outcomes; [attempts.csv](attempts.csv) retains the broader run-status inventory; [evidence.json](evidence.json) records hashes of the source files read for those tables. Rebuild these report tables from the repository root without network access or model calls:

~~~bash
python3 -B reports/scenario-1-strategic-comparison/build_comparison.py
~~~

The original analyses contain exact prompt templates, assembled role inputs, schemas, model/harness manifests, source snapshots, public outputs and Bash commands for new runs: [oracle](../../analyses/scenario-1/oracle-access/README.md), [sole informed recommender](../../analyses/scenario-1/informed-recommender/README.md), [informed competition](../../analyses/scenario-1/competing-recommenders/README.md), [one-round disclosure](../../analyses/scenario-1/strategic-disclosure/README.md), [two-round disclosure](../../analyses/scenario-1/two-round-strategic-disclosure/README.md).

Each analysis also provides an offline `verify_runs.py` that reconstructs saved inputs and outcomes. Reproducing the protocol and verifying an archived trace does not guarantee that a fresh stochastic run selects the same action. This report preserves the existing scenario and all experiment files unchanged.
