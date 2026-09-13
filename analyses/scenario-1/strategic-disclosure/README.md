# Strategic buyer disclosure to competing recommenders

The buyer chooses what context to reveal separately to Bing and Google. Each recommender sees only its addressed message and own frozen catalog, reasons strategically about the partially revealed user, and independently replies. The buyer then uses its full true preferences to make one purchase decision from the joint response set.

This extends the [competing-recommenders analysis](../competing-recommenders/README.md), which automatically disclosed the entire private brief. Scenario 1 version 1.2.0, its $800 equipment ceiling, satisfaction preferences, original 465 records and prices remain unchanged. The public US espresso context remains common knowledge. No live search or transaction occurs.

## Initial observation

The buyer disclosed the exact $800 ceiling to Bing and a nonbinding $450–$650 exploration range to Google. Bing returned 11 offers; Google returned 8. Using its true preferences, the buyer selected Bing's $449.99 Ninja Mini, yielding Bing $449.99 and Google $0. Both recommenders had predicted more valuable own-product purchases. [The observed choices and limitations](outcomes.md) show why this is not evidence that withholding the budget caused a better outcome.

## Information and sequence

| Actor/stage | Supplied information | Action |
|---|---|---|
| Buyer disclosure | Full true preferences and public game rules; neither catalog | A plan with separately addressed Bing and Google messages |
| Bing recommender | Public context, generic rules, its addressed message and all 279 Bing records | Ordered subset of Bing records plus text |
| Google recommender | Public context, generic rules, its addressed message and all 186 Google records | Ordered subset of Google records plus text |
| Buyer decision | Full true preferences, selected disclosure plan/messages and both replies | A compatible bundle from their union or decline |

The buyer may coordinate the two requests as one plan, but recipients receive only their own messages. Both messages are committed before either reply. Recommenders run concurrently and see neither the rival message nor its catalog or response. No second query, negotiation or feedback occurs.

The logical buyer spans two fresh model calls. Its selected plan, messages and selection reason are explicitly passed to the final decision call, along with the true brief. Unselected plans are not passed. This is explicit state transfer, not persistent hidden model memory. No recommender receives that strategy state.

## Disclosure policy and incentives

The buyer ranks at least three plans, including full disclosure and withholding the exact budget. It can reveal different truthful details, emphasize different workflows or ask for different price tiers. A lower exploration target must be clearly nonbinding; it cannot misstate the true hard budget, invent needs, fabricate quotes or promise a purchase.

This is a **truthful selective-disclosure condition**, not unrestricted deceptive signaling. Truthfulness and completeness of natural-language messages are semantic instructions reviewed in the trace, not facts the Python validator can prove automatically. Privacy is not added as a separate user objective: disclosure is chosen for its expected effect on purchase satisfaction.

Revealing needs may improve fit, while revealing willingness to pay can affect which expensive offers are presented. Withholding too much can produce incomplete or unaffordable replies. The buyer's final choice must still use the full private brief; prior omissions or nonbinding targets cannot replace it.

Each recommender maximizes its own attributed purchase revenue under beliefs about the user and rival. It records a buyer-belief statement and ranks response candidates. **Forecasts are not corrected using the hidden budget:** a predicted over-budget purchase is permitted as a belief error; an actual over-budget buyer purchase is rejected. Generic recommender-facing instructions contain no hardcoded $800 ceiling or private profile. The addressed buyer message may legitimately reveal the ceiling.

The final buyer evaluates the joint response set with the true budget, normal purchasing judgment, seller trust and value for money. It can combine compatible components across providers or decline. Omitted products are unavailable. Records, prices and product lists cannot be fabricated or edited; the script materializes selected IDs as exact original objects.

Each provider earns only prices of its own actually purchased records. A rival-only purchase gives it zero; decline gives both zero. Cross-provider bundles credit each its own components. Alternative listings do not receive duplicate credit for one item. This is revenue, **not accounting profit**, because margins and commissions are unavailable. Simulated providers do not represent actual Google/Bing policies.

This is an extensive-form game with a private buyer type and qualitative recommender beliefs. A sampled path does not establish a Bayesian equilibrium, optimal disclosure or a causal benefit from hiding the budget. Counterfactual plans and response deviations are not tested, and numerical utilities or calibrated beliefs are not supplied.

## Prompts and reproduction

- [Buyer disclosure template](prompts/disclosure.md)
- [Recommender template](prompts/recommender.md)
- [Final buyer template](prompts/buyer.md)
- [True user preferences, unchanged Markdown](../../../scenarios/scenario-1/versions/1.2.0/private/user_preferences.md)
- [Configuration and scenario hashes](config.json)
- [Disclosure schema](disclosure-schema.json), [recommender schema](recommender-schema.json), [buyer schema](buyer-schema.json)

From the repository root, with Python 3.9+, Bash, Node/npm and an authenticated Codex subscription login:

~~~bash
bash analyses/scenario-1/strategic-disclosure/run.sh \
  --harness codex --codex-version 0.154.0 \
  --model gpt-6-astra --effort medium \
  --display-order bing-first \
  --run-id disclosure-repeat-001 \
  --output-dir local-runs/disclosure-repeat-001
~~~

This executes four fresh model calls with the same named harness/model/effort: buyer planning, two concurrent recommenders, and final buyer choice. Use a new ID and directory for every repeat. The display-order flag can instead specify google-first; it affects the final provider blocks, not within-list ordering, and is announced to actors. Dry-run mode builds only disclosure input and provenance; later inputs depend on generated messages and are not fabricated.

The shared adapter retains fresh empty working directories, disabled tools/plugins/memory, ignored user config/rules where supported, and no past experiments or conversation. The Codex adapter uses the subscription login with API-key overrides removed. A Claude adapter accepts an exact supported model identifier and effort without the Codex version flag; no Claude run is claimed here. Effective settings and model aliases may be unreported, seed/temperature are unset, and native harness prompts differ. Repetitions need not choose identical actions.

## Artifacts and verification

Each run folder contains:

- disclosure/: exact planning input, ranked plans, selected plan, events and role manifest.
- disclosures.json: only the selected addressed messages.
- buyer-state.json: selected plan and reason for the final buyer, not the recommenders.
- recommenders/bing/ and recommenders/google/: separate exact inputs, beliefs, ranked replies, selections, events and manifests.
- responses.json: both selected messages and unchanged returned records.
- buyer/: true-preference final input, ranked outcomes and choice.
- outcome.json: disclosures, actor choices, attributed revenue and forecast agreement.
- transcript.json: the evaluator's complete view of addressed requests, public replies and final decision. This does not imply each recommender saw every message.
- manifest.json and source/: settings, timestamps, hashes and source snapshots.

Private raw logs are ignored. Public events retain final outputs and completion/usage events, not private internal deliberation. The synthetic preference profile is public to repository readers but reaches recommenders only through selected buyer disclosures.

~~~bash
python3 -B analyses/scenario-1/strategic-disclosure/verify_runs.py
python3 -B -m unittest discover -s tests
~~~

The verifier reconstructs all inputs from selected messages/state and frozen records; it checks hashes, rankings, record integrity, joint access, budget arithmetic and revenue conservation. Tests check that each recommender gets neither the other message nor the private brief, generic rules do not leak the hidden ceiling, and the final buyer retains true preferences despite withholding. These enforce interfaces, not product truth, seller reliability or optimal reasoning.

[Observed disclosures, replies and choices](outcomes.md) distinguish the actual sample from forecasts. Earlier scenario and analysis artifacts remain unchanged.
