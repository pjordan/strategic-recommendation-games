# Interpreting the strategic-learning prompt pilot

The treatment adds a recommender-only instruction to infer preferences from revealed information, consider candidate opportunity costs and reason against a plausible mixture of opposing behavior. It extends the explicit-facts prompt; cards, facts, buyer prompts and the purchase-revenue objective remain fixed. The [results report](results.md) records purchases, selected candidates, stated beliefs and forecasts, with links to the exact traces. The [study README](README.md) supplies the prompt and fresh-run command.

All five games and 18 actor calls completed using Codex CLI 0.154.0 / requested gpt-6-astra / medium. Two purchases and four ordered recommendation lists changed from the historical explicit-facts pilot. All five purchases contained one item.

| Condition | Prior explicit-facts purchase | New purchase | Returned cards, prior/new |
|---|---|---|---:|
| Sole Bing | Kenmore, $764.99 | Same | 1 / 1 |
| Sole Google | Philips 3300, $729.95 | Magnifica Start, $769.00 | 1 / 1 |
| Informed competition | Breville Impress, $649.99 | Same | 3 / 5 |
| Strategic disclosure | Ninja Premier, $599.99 | Ninja Mini, $449.99 | 15 / 10 |
| Two rounds | Ninja Mini, $449.99 | Same | 10 / 15 |

## What the selected actions show

Sole Bing retained the $764.99 Kenmore singleton. It considered acceptance by a buyer who found the fit adequate versus refusal by a buyer emphasizing savings or espresso-brand confidence, then selected the larger credible sale. The buyer purchased it. The instruction did not eliminate strategic omission.

Sole Google changed from the prior $729.95 Philips to a $769 Magnifica Start singleton. It described buyers who emphasize convenience, seller confidence or hands-on preparation, and judged the larger sale worth its marketplace-seller acceptance risk. The buyer accepted. The prior Philips was absent from the new buyer's list, so this is a change in the recommender's selected offer, not a direct buyer comparison of those two products.

Under informed competition, the visible selection expanded from three to five cards, but the buyer retained the $649.99 Target-listed Breville Impress. Bing added the $599.99 Ninja Premier as a fallback against an unseen rival; Google preserved several higher-priced options while explicitly omitting the cheaper Chefman to avoid displacing a larger sale. These reported tradeoffs show that broader coverage and continued omission can coexist.

With strategic initial disclosure, the purchase changed from the $599.99 Ninja Premier to Google's $449.99 Ninja Mini. Both providers received the true $800 ceiling through the selected buyer messages. They returned ten cards in total, down from fifteen in the reference, and each forecast a larger own sale. The buyer instead judged the Mini's grinding, dosing assistance and manual steaming the best value. The Premier remained available, but other messages and lists also changed; this is not a controlled test of one sentence's persuasive effect.

## The two-round sequence

The buyer disclosed its $800 ceiling to both providers and requested options across price levels. Each recommender returned six cards. The buyer then shared selected rival cards and attributed facts, asking providers to justify workflow, cleaning and seller-confidence premiums without inventing a lower budget.

Bing moved from a Ninja-led recommendation toward its $349.99 automatic VEVOR and added a previously omitted $259.99 semi-automatic VEVOR. Google led with the $449.99 Mini and added a $399.99 Chefman Deluxe and $332.49 automatic VEVOR. Both described balancing potential larger sales against losing buyers seeking better value. In total, three previously omitted record IDs appeared in round 2, bringing the final available set to fifteen; every first-round offer remained available.

The buyer still selected the Mini, narrowly preferring its integrated weighing to the $329.99 Chefman Supreme's savings. It did not equate value with the cheapest qualifying offer. Google's final $449.99 own-revenue forecast matched; Bing's $349.99 forecast did not, and Bing earned zero. The additional offers changed the comparison without changing the purchased record relative to the explicit-facts baseline. See the [full two-round interaction](runs/codex-astra-medium-pilot-001/two-round-strategic-disclosure-r001/text-enabled/transcript.json).

## What this dimension measures

The transcripts expose agents' reported acceptance-risk and substitution tradeoffs. They do not measure external regret: the alternative candidate responses were never executed against the same opposing behavior. Forecast-versus-realized revenue is included for inspection, but is not regret, and later moves can intervene after a first-round forecast.

No opponent-frequency estimator, repeated-game update rule, payoff matrix or convergence test runs in this condition. The agents receive no earlier games. Their mixtures are qualitative beliefs rather than empirical frequencies. This pilot therefore evaluates a combined instruction inspired by no-regret and fictitious play, not the performance of either algorithm.

The historical comparison also mixes the instruction change with fresh model sampling. In particular, the initial buyer prompt is unchanged and does not announce the additional recommender instruction, yet can generate different opening messages. One sample per condition cannot identify a causal effect, distinguish the prompt's component ideas, or establish an optimal strategy. Lower spending does not by itself demonstrate increased satisfaction.
