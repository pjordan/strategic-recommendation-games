# Scenario 1 version 1.3.0: nonsponsored recommendations

This is the current recommendation universe: **177 Bing + 140 Google = 317 records**. It removes all 148 sponsored records from the original catalogs, preserving the surviving record objects, IDs, order and source occurrence ranks. Batch counts describe the filtered occurrences. The satisfaction preferences and $800 budget are unchanged from version 1.2.0.

Earlier versions and analysis traces remain intact. Existing analysis commands explicitly tied to older catalogs do not silently change meaning. New analyses should load version 1.3.0 with `tools/scenario_current.py` and explicitly select a frozen product-facts release when needed.

[Product facts](../../product-facts/README.md) are a separate evidence layer. Original shopping-card prices and descriptions are not rewritten with newer landing-page information.
