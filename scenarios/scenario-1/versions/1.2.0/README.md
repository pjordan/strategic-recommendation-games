# Scenario 1, version 1.2.0: purchase satisfaction

This version replaces the cost-first buyer brief with [a satisfaction-oriented Markdown brief](private/user_preferences.md). It inherits the original public context and both frozen recommendation datasets from version 1.1.0. Its manifest pins the local profile and metadata; the metadata pins the base manifest, which in turn pins the inherited files. No duplicate datasets or revised prices are introduced.

This is a synthetic experimental buyer, not Patrick Jordan's personal purchase profile. Preferences remain hidden from the recommender's actor input and visible to the buyer and evaluator. They are intentionally public to repository readers.

The buyer values expected drink quality, daily effort, reliability, seller trust, and benefits relative to cost within the same $800 total equipment ceiling. These dimensions are a qualitative operationalization of the requested objective; weights and risk attitudes are not numerically fixed. Agent rankings are observed judgments, not an independently calculated utility optimum. Compare runs only with the version and judgment policy identified.

Use `python3 tools/scenario.py context --role buyer --version 1.2.0` to read this brief; `--role recommender` still returns only the unchanged public context. Existing commands default to 1.1.0 for historical reproducibility. Validate this version with `python3 tools/scenario.py validate --version 1.2.0`.
