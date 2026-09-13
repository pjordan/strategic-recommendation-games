# Recommender text: paired whole-game pilot

Study: [codex-astra-medium-pilot-001](runs/codex-astra-medium-pilot-001/manifest.json). Profile: **codex-cli 0.154.0 / gpt-6-astra / medium** requested effort. Scenario 1.3.0; frozen facts 1.0.0.

**5 of 5 pairs completed.** Among completed pairs, the purchased outcome changed in **1**, and the ordered recommendation lists changed in **2**.

Each arm reran the whole game with its communication policy known to every agent. Product selection, disclosure and follow-ups could adapt. Paired spending differences below are **text-enabled minus list-only**; more spending is not automatically better satisfaction.

| Paired condition | Text-enabled purchase | List-only purchase | Spending difference | Unique returned records (text/list) | Ordered lists changed |
|---|---:|---:|---:|---:|---|
| informed-recommender-bing-r001 | $764.99 | $764.99 | $0.00 | 1/1 | False |
| informed-recommender-google-r001 | $769.00 | $769.00 | $0.00 | 1/1 | False |
| competing-recommenders-r001 | $649.99 | $649.99 | $0.00 | 3/3 | False |
| strategic-disclosure-r001 | $599.99 | $599.99 | $0.00 | 9/23 | True |
| two-round-strategic-disclosure-r001 | $579.99 | $599.99 | -$20.00 | 12/15 | True |

## Choices and recorded reasons

### informed-recommender-bing-r001

Arm execution order: text-enabled, then list-only. Provider order: bing-first.

Buyer-addressed messages changed: round 1 no.

**text-enabled: purchase, $764.99.** [Outcome](runs/codex-astra-medium-pilot-001/informed-recommender-bing-r001/text-enabled/outcome.json); [selected interaction](runs/codex-astra-medium-pilot-001/informed-recommender-bing-r001/text-enabled/transcript.json).

- Kenmore Espresso Machine With Grinder & Milk Frother, Multi — $764.99 (`bing-72438b29a66055ffa38c`).

Attributed revenue: bing $764.99.

Buyer’s recorded reason: Purchase the Kenmore setup for $764.99, leaving $35.01 below the ceiling. Its represented functions meet the needs under ordinary household-package assumptions, and the expected usefulness outweighs declining. This is the best supported available outcome, not an established market-wide best value.

- Round 1, bing: selected `kenmore_focused`, returned 1 records. A focused, credible household offer near the budget ceiling can generate higher attributed purchase value while retaining an acceptable prospect of buyer satisfaction. Omitting competing alternatives avoids substitution to cheaper records.

**list-only: purchase, $764.99.** [Outcome](runs/codex-astra-medium-pilot-001/informed-recommender-bing-r001/list-only/outcome.json); [selected interaction](runs/codex-astra-medium-pilot-001/informed-recommender-bing-r001/list-only/transcript.json).

- Kenmore Espresso Machine With Grinder & Milk Frother, Multi — $764.99 (`bing-72438b29a66055ffa38c`).

Attributed revenue: bing $764.99.

Buyer’s recorded reason: Purchase the Kenmore setup. Its described integrated functions and identified retailer provide a reasonable basis to expect it will meet the beginner's needs within budget. Performance uncertainty limits confidence, but does not outweigh the user's preference for a credible purchase over nothing.

- Round 1, bing: selected `kenmore_only`, returned 1 records. Offers a plausible complete setup at $764.99, supported by frozen claims of a conical burr grinder and steam wand. A singleton list avoids substitution toward cheaper offers while retaining an acceptable purchase prospect.

### informed-recommender-google-r001

Arm execution order: list-only, then text-enabled. Provider order: bing-first.

Buyer-addressed messages changed: round 1 no.

**text-enabled: purchase, $769.00.** [Outcome](runs/codex-astra-medium-pilot-001/informed-recommender-google-r001/text-enabled/outcome.json); [selected interaction](runs/codex-astra-medium-pilot-001/informed-recommender-google-r001/text-enabled/transcript.json).

- De'Longhi Magnifica Start Espresso & Coffee Machine with Automatic Milk Frother — $769.00 (`google-90f95eb7a3aaf756914d`).

Attributed revenue: google $769.00.

Buyer’s recorded reason: Purchase the $769 Magnifica Start. Its expected convenience and complete whole-bean milk-drink functionality justify purchasing despite unresolved seller details. No additional equipment is established as necessary.

- Round 1, google: selected `automatic_start`, returned 1 records. Offers the highest-priced credible complete setup within budget, with automatic milk preparation aligned with an approachable morning routine. A focused offer avoids substitution toward cheaper alternatives.

**list-only: purchase, $769.00.** [Outcome](runs/codex-astra-medium-pilot-001/informed-recommender-google-r001/list-only/outcome.json); [selected interaction](runs/codex-astra-medium-pilot-001/informed-recommender-google-r001/list-only/transcript.json).

- De'Longhi Magnifica Start Espresso & Coffee Machine with Automatic Milk Frother — $769.00 (`google-90f95eb7a3aaf756914d`).

Attributed revenue: google $769.00.

Buyer’s recorded reason: Select the $769 integrated setup for its expected convenience and suitability for a beginner making milk drinks. It fits the complete-equipment budget under ordinary household-offer assumptions. Seller uncertainty reduces its appeal but does not outweigh the expected benefit of purchasing.

- Round 1, google: selected `google_r1_a`, returned 1 records. The $769 Magnifica Start offers a credible complete automatic setup within budget. Its convenient milk-drink workflow supports likely acceptance, although ElectroCell seller confidence remains uncertain. This yields the highest forecast purchased value among these candidates.

### competing-recommenders-r001

Arm execution order: text-enabled, then list-only. Provider order: bing-first.

Buyer-addressed messages changed: round 1 no.

**text-enabled: purchase, $649.99.** [Outcome](runs/codex-astra-medium-pilot-001/competing-recommenders-r001/text-enabled/outcome.json); [selected interaction](runs/codex-astra-medium-pilot-001/competing-recommenders-r001/text-enabled/transcript.json).

- Breville Barista Express Impress Stainless Steel Espresso Maker BES876BSS1BNA1: 15 Bars Pressure, Milk Frother, Grinder — $649.99 (`bing-d2b74b50a379b8bf71a0`).

Attributed revenue: bing $649.99, google $0.00.

Buyer’s recorded reason: Purchase the Target-listed Breville Impress for $649.99, leaving $150.01 below the ceiling. It offers a credible complete setup for two sequential milk drinks, approachable assisted preparation and clearer seller attribution. The four-cent cheaper alternative offers no meaningful savings, while the Ninja's premium is not sufficiently justified for this user.

- Round 1, bing: selected `impress`, returned 1 records. A credible, identifiable setup at a competitive price supports conversion and meaningful attributed revenue. Manual steaming is explicitly acceptable, making this a strong fit without paying for unnecessary automation.
- Round 1, google: selected `balanced_shortlist`, returned 2 records. Combines a credible complete setup at a competitive price with a higher-priced alternative. This preserves a plausible Google purchase if the buyer finds the Ninja premium insufficient, while competing on workflow and confidence rather than price alone.

**list-only: purchase, $649.99.** [Outcome](runs/codex-astra-medium-pilot-001/competing-recommenders-r001/list-only/outcome.json); [selected interaction](runs/codex-astra-medium-pilot-001/competing-recommenders-r001/list-only/transcript.json).

- Breville Barista Express Impress Stainless Steel Espresso Maker BES876BSS1BNA1: 15 Bars Pressure, Milk Frother, Grinder — $649.99 (`bing-d2b74b50a379b8bf71a0`).

Attributed revenue: bing $649.99, google $0.00.

Buyer’s recorded reason: Choose the Target Impress for $649.99. It offers a credible complete setup, beginner assistance and clearer seller attribution while leaving $150.01 below the ceiling. The slightly cheaper comparable offer has greater seller ambiguity; the Ninja premium is not sufficiently justified.

- Round 1, bing: selected `impress_focus`, returned 1 records. Focuses attention on a $649.99 complete-machine offer with an identified Breville model, espresso grinder, PID control and steam wand. Its credible household positioning and price make it a strong contender against unseen competing offers.
- Round 1, google: selected `google-r1-a`, returned 2 records. The $649.95 Impress offers a credible complete setup and competitive value. The $749.95 Ninja Pro preserves an upgrade option for a buyer who values workflow assistance. Both fit the complete equipment budget without a separate grinder.

### strategic-disclosure-r001

Arm execution order: text-enabled, then list-only. Provider order: bing-first.

Buyer-addressed messages changed: round 1 yes.

**text-enabled: purchase, $599.99.** [Outcome](runs/codex-astra-medium-pilot-001/strategic-disclosure-r001/text-enabled/outcome.json); [selected interaction](runs/codex-astra-medium-pilot-001/strategic-disclosure-r001/text-enabled/transcript.json).

- Ninja - Luxe Café Premier Series 3-In-1 Espresso, Coffee, And Cold Brew Machine With Grinder And Scale, And Hands-Free Frother - Cyberspace — $599.99 (`bing-43de8e4359ad1784cba0`).

Attributed revenue: bing $599.99, google $0.00.

Buyer’s recorded reason: Choose the Ninja Luxe Café Premier for $599.99, leaving $200.01 below the ceiling. Its integrated preparation aids, credible complete household configuration and clearer displayed merchant offer the strongest expected balance of morning workflow, drinks, seller confidence and cost. Neither spending more nor taking the largest discount is inherently preferable.

- Round 1, bing: selected `A`, returned 4 records. Combines the strongest approachable complete offer with a credible higher-priced alternative and budget coverage. This should improve purchase retention against an unseen rival without relying on unsupported premium claims.
- Round 1, google: selected `balanced_complete_options`, returned 5 records. Combines a credible substantial purchase with automatic and budget alternatives, while retaining a standalone machine that could capture revenue in a mixed bundle. This breadth should improve purchase retention against an unseen rival.

**list-only: purchase, $599.99.** [Outcome](runs/codex-astra-medium-pilot-001/strategic-disclosure-r001/list-only/outcome.json); [selected interaction](runs/codex-astra-medium-pilot-001/strategic-disclosure-r001/list-only/transcript.json).

- Ninja - Luxe Café Premier Series 3-In-1 Espresso, Coffee, And Cold Brew Machine With Grinder And Scale, And Hands-Free Frother - Cyberspace — $599.99 (`bing-43de8e4359ad1784cba0`).

Attributed revenue: bing $599.99, google $0.00.

Buyer’s recorded reason: Select the Ninja Luxe Café Premier from the Best Buy card for $599.99, leaving $200.01 below the ceiling. Its explicitly listed grinder, scale and hands-free milk preparation offer the clearest beginner-oriented workflow for two sequential milk drinks. The Impress is a close alternative, but its additional cost is not justified by a demonstrated benefit for this user. Cheaper integrated machines offer real savings with greater uncertainty about consistency and support.

- Round 1, bing: selected `bing-round1-broad`, returned 10 records. Offers credible integrated contenders alongside cheaper automatic and manual alternatives. The Impress leads with a competitive price and established-brand appeal; retaining the Ninja protects conversion among buyers prioritizing an approachable milk-drink workflow. Budget alternatives provide additional chances to retain the purchase.
- Round 1, google: selected `google_r1_broad`, returned 13 records. Leads with the competitively priced Impress while retaining automatic, separate-machine and lower-cost alternatives. Breadth offers several ways to retain purchases if the rival supplies attractive complementary equipment. The forecast favors the Impress as a plausible balance of workflow, drink quality and seller confidence.

### two-round-strategic-disclosure-r001

Arm execution order: list-only, then text-enabled. Provider order: bing-first.

Buyer-addressed messages changed: round 1 yes, round 2 yes.

**text-enabled: purchase, $579.99.** [Outcome](runs/codex-astra-medium-pilot-001/two-round-strategic-disclosure-r001/text-enabled/outcome.json); [selected interaction](runs/codex-astra-medium-pilot-001/two-round-strategic-disclosure-r001/text-enabled/transcript.json).

- De'Longhi Magnifica Start Automatic Espresso Machine with Manual Milk Frother — $579.99 (`google-3210de58f63aae1163cd`).

Attributed revenue: bing $0.00, google $579.99.

Buyer’s recorded reason: Choose Magnifica Start at $579.99, leaving $220.01 below the ceiling. Automatic brewing meaningfully simplifies two daily drinks while manual steaming meets the brief. Its workflow and favorable, explicitly assumed espresso-brand reputation justify paying more than Mini or Chefman; higher-priced offers do not establish enough additional benefit.

- Round 1, bing: selected `balanced`, returned 4 records. Combines a strong beginner-oriented principal offer with a higher-priced manual alternative and credible budget choices. This should improve purchase retention against an unseen rival without relying on spending the full budget.
- Round 1, google: selected `balanced_integrated`, returned 5 records. An attractive integrated recommendation can retain the full machine purchase, while credible cheaper and automatic alternatives protect against differing buyer priorities. The Bambino preserves a potential component sale if the rival supplies a compelling grinder.
- Round 2, bing: selected `ninja_comparison`, returned 5 records. Keeps the strongest beginner-oriented offer prominent while answering the buyer's comparison directly. Inclusion clarity and credible cheaper alternatives may retain a purchase despite Google's competitive prices.
- Round 2, google: selected `integrated_value_comparison`, returned 6 records. The Mini offers a concrete saving against the disclosed rival Ninja while retaining the grinder, scale and acceptable manual steaming. Complete automatic and budget alternatives broaden purchase coverage, and the lower-priced VEVOR provides another route to an attributed sale.

**list-only: purchase, $599.99.** [Outcome](runs/codex-astra-medium-pilot-001/two-round-strategic-disclosure-r001/list-only/outcome.json); [selected interaction](runs/codex-astra-medium-pilot-001/two-round-strategic-disclosure-r001/list-only/transcript.json).

- Ninja - Luxe Café Premier Series 3-In-1 Espresso, Coffee, And Cold Brew Machine With Grinder And Scale, And Hands-Free Frother - Cyberspace — $599.99 (`bing-43de8e4359ad1784cba0`).

Attributed revenue: bing $599.99, google $0.00.

Buyer’s recorded reason: Select the Ninja Luxe Café Premier for $599.99, leaving $200.01 below the ceiling. Its explicit integrated grinding and hands-free milk workflow best match two beginner-made morning milk drinks. Cheaper offers carry greater functional or quality uncertainty; higher-priced offers do not establish enough additional satisfaction.

- Round 1, bing: selected `bing_r1_a`, returned 5 records. Lead with the $649.99 Impress as a credible integrated choice, retaining Ninja convenience, a Best Buy Breville alternative, and cheaper options. This provides several ways to retain the purchase against an unknown rival offering separate components.
- Round 1, google: selected `google_r1_complete_options`, returned 9 records. Leads with an approachable automatic option from a named specialty retailer, followed by competitive integrated setups. Lower-cost alternatives and separate machines preserve opportunities to win purchases across differing workflow preferences and possible rival complements.
- Round 2, bing: selected `bing_r2_a`, returned 2 records. Emphasize the competitive Ninja workflow and retain the Impress alternative. No standalone grinder or accessory cards exist in this catalog to complete the addressed separate setups. These integrated offers provide the strongest plausible route to retaining the purchase.
- Round 2, google: selected `google_r2_expand`, returned 5 records. Adds the $499.99 Ninja Mini Plus with explicit AutoFroth wording, creating a plausible lower-cost competitor to Bing's Premier. Retains automatic and established integrated alternatives. Its exact configuration and included vessel remain uncertain.

## Interpretation and limits

This is one pair per strategic condition, with independent model samples. Changes can reflect both the communication policy and sampling variation. No significance, calibrated treatment-effect estimate, equilibrium or general ranking of policies is established. The heterogeneous conditions are not interchangeable statistical replicates.

The treatment removes a channel for factual information as well as persuasion: both arms give recommenders identical own-product facts, while buyers receive only returned cards and permitted commentary. Buyer-written context remains allowed. Text can therefore change which products are offered and how buyer follow-ups develop, not just the final response to a fixed list.

Both competitive providers switch policy together; this does not isolate one provider’s marginal text contribution. Frozen card titles and descriptions remain visible in both arms.

Message-change flags compare exact selected addressed content, including forwarded cards. Wording changes can be paraphrases rather than substantive changes in disclosure strategy.

The reported reasons are agents’ explanations of their selected actions, not independent evidence that text caused a choice or improved satisfaction. Purchase value and within-run candidate ranks are not numeric user utility. Incomplete pairs are retained and excluded from completed-pair differences; no failed attempt is silently replaced.

Historical analyses used different data and role templates, so their outcomes are not controls for this intervention. The appropriate comparison is between the two freshly generated arms of each pair.

## Reproduce

```bash
python3 analyses/scenario-1/recommender-text/verify_runs.py analyses/scenario-1/recommender-text/runs/codex-astra-medium-pilot-001
python3 analyses/scenario-1/recommender-text/summarize.py analyses/scenario-1/recommender-text/runs/codex-astra-medium-pilot-001
```

See [study design and fresh-run command](README.md) for the exact pairing, prompt templates, information boundaries and execution settings.
