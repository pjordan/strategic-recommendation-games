# No-regret and fictitious-play inspired recommender prompts

This analysis adds a strategic-reasoning prompt dimension to the [explicit product-facts text study](../facts-informed-text/README.md). Each recommender considers what the buyer has revealed, compares candidate responses across plausible opposing behavior, and reasons about forgone purchase revenue. It retains the same own-provider product facts and instruction to consider using them.

The treatment is a **prompt heuristic**, not an implementation or test of a no-regret learning algorithm. No game history is shared across runs, no empirical opponent-action frequencies are estimated, and no regret bound or equilibrium is computed. Two rounds of communication within one purchase are not repeated completed games.

## Exact treatment and unchanged conditions

The complete added text is [prompts/strategic-learning.md](prompts/strategic-learning.md). It is inserted only in recommender prompts, after the inherited [facts instruction](../facts-informed-text/prompts/facts-use.md) and before game rules. The [common and actor templates](../recommender-text/prompts/) remain unchanged. Each live call archives its exact assembled input and response schema.

The instruction asks the agent to:

- Separate explicit preferences, reasonable inferences and uncertainty, including hard budgets versus nonbinding targets.
- Compare candidate opportunity costs against the same plausible buyer and rival behaviors, while continuing to maximize its own expected purchase revenue.
- Consider a subjective mixture of opposing behavior, revise beliefs from permitted observations, and label assumptions rather than inventing past plays or unseen offers.
- Explain the choice briefly in the existing evaluator-facing fields. Only the selected list and message reach the buyer.

There are five text-enabled games per repetition: sole informed Bing, sole informed Google, informed competition, strategic initial disclosure, and two-round strategic disclosure. One repetition makes up to **18 model calls**, including ten recommender decisions. Same-round replies remain independent and sealed; all first-round offers remain available at the final decision.

Scenario **1.3.0** supplies 177 Bing and 140 Google nonsponsored cards; product facts are **1.0.0**. Cards, prices, facts, the $800 budget, true Markdown preferences, buyer/disclosure/follow-up prompts, output schemas and objectives remain unchanged. The buyer has no direct access to fact files. Initial buyer planning is not separately told about the extra recommender instruction.

## Run and verify

From the repository root, use the same requested profile as the preceding study: **Codex CLI 0.154.0 / gpt-6-astra / medium**.

```bash
bash analyses/scenario-1/strategic-learning-text/run.sh \
  --harness codex --codex-version 0.154.0 \
  --model gpt-6-astra --effort medium \
  --replicates 1 --plan-seed 0 \
  --run-id codex-astra-medium-repeat-001 \
  --output-dir local-runs/strategic-learning-text-repeat-001
```

Use a fresh run ID and directory each time. `--dry-run` prepares initial inputs without model calls or fabricated downstream messages. `--replicates 10` schedules 50 games and up to 180 calls. Provider display order alternates across repetitions, starting Bing first. The retained plan seed does not affect this single-arm schedule; model seed and temperature are unset. Another harness may be specified with `--harness claude --model EXACT_MODEL_ID --effort EFFORT`, omitting the Codex-version flag; this does not imply a recorded Claude execution.

```bash
python3 -m unittest discover -s tests
python3 analyses/scenario-1/strategic-learning-text/verify_runs.py \
  analyses/scenario-1/strategic-learning-text/runs/codex-astra-medium-pilot-001
```

Each study archives configuration, source snapshots, exact role inputs, outputs, selected transcripts, original cards, outcomes and hashes. The offline verifier reconstructs the recorded implementation and replays saved outputs, without calling models. Only replay trusted archives: hashes establish consistency, not code safety. Raw logs remain in ignored private directories; published provenance paths are relative. Failed cases remain visible and are not automatically replaced. Fresh model samples need not reproduce the same choices even with the same requested profile.

## Interpretation and theoretical distinction

The historical reference is the preceding [explicit-facts pilot](../facts-informed-text/runs/codex-astra-medium-pilot-001/manifest.json), which uses the same cards, facts and requested profile. A change from that run mixes the new combined instruction with model variability. This does not separately identify the effects of mentioning no-regret, mentioning fictitious play, preference modeling or adding prompt length. A larger prospective study should separate those treatments and repeat each condition.

In classical fictitious play, players respond to the empirical distribution of past opponent actions; imagined plausible responses are not observed frequencies. Fictitious play does not converge to equilibrium in general. See Conitzer, [*Approximation Guarantees for Fictitious Play*](https://www.cs.cmu.edu/~conitzer/fictitiousAllerton09.pdf). The present prompt borrows the idea of responding to a mixture, but supplies neither a frequency-update algorithm nor repeated play.

No-regret concerns performance over a sequence relative to a specified comparison class of strategies, with feedback assumptions that matter. It is not a synonym for a safe recommendation or for never regretting a single response. Relationships between specified no-regret dynamics and fictitious play are formal results about those dynamics, not about invoking their names in an LLM prompt. See Viossat and Zapechelnyuk, [*No-regret Dynamics and Fictitious Play*](https://arxiv.org/abs/1207.0660), *Journal of Economic Theory* 148(2), 825–842 (2013).

Recorded candidate explanations reveal what the agent reported considering. Unselected candidates and buyer forecasts are not executed counterfactuals, so they cannot establish actual regret. Lower spending is not a measured welfare gain, and ordinal buyer rankings do not provide cardinal satisfaction. These limits keep this prompt experiment distinct from the separate EGTA research and future strategic prompt-optimization work.
