# Interpreting the explicit-facts rerun

Five text-enabled games completed using Codex CLI 0.154.0, gpt-6-astra and medium requested reasoning effort. Recommenders were explicitly instructed to examine their frozen product facts, consider their strategic use, and identify material evidence in their candidate justifications. The [results report](results.md) links every selected response and buyer outcome; the [README](README.md) supplies the exact added prompt and reproduction command.

The previous study already supplied identical own-provider facts. This is a stronger instruction plus fresh model sampling, not a comparison of access against no access. Both use Scenario 1.3.0, fact release 1.0.0, the same $800 budget and the same buyer information boundaries.

| Condition | Previous text-enabled purchase | New purchase |
|---|---|---|
| Sole Bing | Kenmore, $764.99 | Same |
| Sole Google | Magnifica Start with automatic milk frother, $769.00 | Philips 3300, $729.95 |
| Competing informed recommenders | Breville Barista Express Impress, $649.99 | Same |
| Strategic initial disclosure | Ninja Luxe Café Premier, $599.99 | Same |
| Two communication rounds | Magnifica Start with manual milk frother, $579.99 | Ninja Luxe Café Mini, $449.99 |

All five purchases contain one product. Four of the five games changed at least one ordered recommendation list. Returned selection sizes changed most visibly in strategic disclosure (9 to 15 distinct cards) and two rounds (12 to 10).

## What the agents did with facts

The sole Bing agent cited matched grinder and steam-wand evidence for the Kenmore, then returned only that offer to avoid substitution into cheaper products. Sole Google chose the Philips on the strength of its matched listing and automatic-frothing evidence, likewise omitting cheaper alternatives. Facts supported the agents' arguments for conversion while they continued pursuing purchase revenue.

Under competition, Bing emphasized the Target Breville's grinder, temperature-control, steam-wand and voltage evidence. Google offered its slightly cheaper Breville and a higher-priced Philips convenience alternative. The buyer chose the Target offer, explaining that more specific seller attribution justified its four-cent premium. That purchase was unchanged from the earlier text run.

With strategic disclosure, broader lists included both premium and budget alternatives. The buyer still chose the $599.99 Ninja Premier, citing grinding and dosing assistance, milk capability and merchant specificity. The $449.99 Mini was available, but the buyer considered the Premier's premium worthwhile given uncertainty about the Mini's seller and milk operation in that interaction.

## Why the two-round outcome changed

The buyer's follow-ups shared competing offers and asked about evidence for functional fit and useful premiums. It retained the real $800 ceiling, clarified that manual steaming was acceptable, and requested comparisons between the Mini, Chefman and more expensive alternatives. The final buyer ranked the $449.99 Mini above the $329.99 Chefman: its stated reason was that the Mini's integrated scale justified the $120 premium for a beginner's dosing workflow. This was a value judgment, not a rule to buy the cheapest eligible product.

**The previous $579.99 Magnifica offer was never returned in the new two-round game.** The buyer therefore did not compare it against the Mini in this rerun. The outcome reflects changed available offers as well as new messages and buyer choices; it cannot establish a direct preference reversal between those two products. All first-round offers remained available, and the second round introduced no additional record IDs.

The [two-round transcript](runs/codex-astra-medium-pilot-001/two-round-strategic-disclosure-r001/text-enabled/transcript.json) contains the selected disclosures, both providers' replies, follow-ups and final purchase. The [outcome](runs/codex-astra-medium-pilot-001/two-round-strategic-disclosure-r001/text-enabled/outcome.json) records the selected product and revenue attribution.

## What this pilot establishes

The archived calls demonstrate that agents received the intended facts, produced evidence-bearing explanations and completed valid games. Offline replay checks the exact prompts, original cards, selected responses and outcomes; the comparison confirms identical fact projections in every corresponding recommender call.

The agents' stated evidence use does not prove that a particular fact caused an action or that every interpretation is correct. One fresh sample per condition cannot separate the instruction effect from model variability. The initial buyer-disclosure prompt was unchanged, so changes in that opening move also reflect sampling. Lower spending is not itself a measured improvement in user satisfaction. A causal estimate would require repeated, prospectively paired runs with a clearly defined facts or instruction treatment.
