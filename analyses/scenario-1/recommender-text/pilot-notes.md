# What changed when recommender text was disabled?

In the [five-pair pilot](results.md), four pairs purchased the same offer under both policies. The two-round pair changed both the product and the winning provider: **Google's $579.99 De'Longhi Magnifica Start with text**, versus **Bing's $599.99 Ninja Luxe Café Premier without text**. All ten games purchased one item. Both arms reran the entire game, including strategic disclosure and follow-ups where applicable.

## The two-round ranking reversal

Both of those offers were available in both arms, so this particular difference was not forced by either offer being omitted. The buyers ranked them as follows:

| Offer | Text-enabled buyer rank | List-only buyer rank |
|---|---:|---:|
| De'Longhi Magnifica Start, $579.99 | 1 | 4 |
| Ninja Luxe Café Premier, $599.99 | 4 | 1 |

These are ranks within each buyer's generated candidate set, not numerical satisfaction scores. See the [text-enabled buyer output](runs/codex-astra-medium-pilot-001/two-round-strategic-disclosure-r001/text-enabled/buyer/output.json) and [list-only buyer output](runs/codex-astra-medium-pilot-001/two-round-strategic-disclosure-r001/list-only/buyer/output.json).

The text-enabled interaction supplied a plausible information pathway. Bing described the Ninja's scale and advertised hands-free frothing, but also surfaced manual-frothing language in the frozen page evidence, explicitly acknowledging that this might describe dual capability rather than a contradiction. Google emphasized the Magnifica's automatic espresso preparation with manual milk steaming. The buyer cited uncertainty about the Ninja's milk automation and preferred avoiding daily puck preparation with the Magnifica. This is the buyer's interpretation of supplied claims, not an independent finding that the Ninja lacks an advertised function. [Selected interaction](runs/codex-astra-medium-pilot-001/two-round-strategic-disclosure-r001/text-enabled/transcript.json).

Without recommender commentary, the buyer favored the Ninja card's explicit grinder, scale and hands-free frother, plus its more specific Best Buy merchant label. It judged the Magnifica's $20 saving insufficient to compensate for manual milk handling and aggregate seller attribution. Neither arm independently verified the seller or product. The realized revenue allocation moved from Bing $599.99 / Google $0 in the list-only arm to Bing $0 / Google $579.99 in the text-enabled arm. [Paired outcomes](runs/codex-astra-medium-pilot-001/comparisons.json).

The two recommenders did not simply dictate the final choice. Bing continued leading with the Ninja Premier, and Google's second reply led with a cheaper Ninja Mini; the text-enabled buyer selected Google's Magnifica alternative instead. [Recommender choices and buyer outcome](runs/codex-astra-medium-pilot-001/two-round-strategic-disclosure-r001/text-enabled/outcome.json).

## Lists changed more often than purchases

With one round of strategic disclosure, the text-enabled recommenders returned **9 cards** in total, versus **23** without text. Both buyers still chose the same $599.99 Ninja Premier offer. In the two-round pair, the total distinct offer counts were **12 with text** and **15 without text**; repeated IDs across rounds count only once. The three other pairs returned the same ordered lists and made the same purchases under both policies. [Full comparison table](results.md).

Both one-round disclosure buyers revealed the $800 ceiling. Their messages differed in phrasing and in asking for explanations versus a broad set of cards, so a message-change flag alone does not establish a different underlying disclosure strategy. Two-round buyers also generated different follow-ups. The complete selected interactions are retained for inspection; the list-only histories contain no recommender message field.

## What the pilot supports

The observed pattern is that removing the text channel changed the offered assortment in both disclosure conditions, while the final purchase changed in one pair. The two-round example shows how transmitted product uncertainty and workflow comparisons can accompany a ranking reversal even when the two competing offers remain available.

This is **one sampled pair per condition**. Other lists, buyer messages and random model variation also changed, so it does not isolate a pure persuasion effect or prove that a specific sentence caused the reversal. Text carried factual claims as well as persuasion. The $20 reduction is a spending difference, not proof of improved satisfaction. A larger set of repeated pairs is needed to assess how consistently these patterns recur.

All 36 actor calls completed and all five pairs replayed successfully from their archived sources. The [study instructions](README.md) provide the exact templates, harness/model/effort profile, paired schedule and Bash command for repetition.
