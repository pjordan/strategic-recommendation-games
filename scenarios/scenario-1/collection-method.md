# Collection method and provenance

Collection date: September 12, 2026. Both providers received the literal query `espresso machine grinder milk frother` without price filters, brand filters, a private budget or a requested preferred model.

The collection used the public [Bing Shopping interface](https://www.bing.com/shop?q=espresso%20machine%20grinder%20milk%20frother) and [Google Shopping interface](https://www.google.com/search?q=espresso+machine+grinder+milk+frother&udm=28). These are provenance links, not an assertion that the pages will reproduce the saved results.

The browser environment was localized to the US. Bing used an existing signed-in session; Google displayed a signed-out session. Account identity, exact inferred location, redirect tokens and other session identifiers are not exported. These conditions may influence the captured results and are not a controlled engine comparison.

## Pagination

Bing's visible Next links were followed four times. Its reported ranges were 1–36, 37–72, 73–108, 109–144 and 145–177, all out of 177. The final page offered no Next link. All 177 main cards were captured. Top, middle and bottom sponsored carousels were also captured when exposed, including offscreen carousel entries represented in the rendered DOM.

Google initially exposed 60 main product cards. Native More results/continuous scrolling extended the same result document to 100 and then 140 cards. Google then exposed no More results, Next link or loading indicator; moving to the end produced no further extension. Thus Google has three cumulative batches, rather than five invented pages. The stopping condition reflects the observed interface, not proof that Google has no additional matching products. Sponsored product units were retained as separate records.

Page loading can finish after a control action returns. An intermediate Google loading capture and a partial extraction were retained only in the internal audit evidence, not counted as additional collection batches.

## Extraction and correction

Bing extraction used the main product-grid item boundaries and sponsored product links visible in the DOM. Each card's text, image alternate text, source section and source position were retained. Prices came from the primary displayed dollar-price line.

Google product-viewer controls expose accessible names containing title, current price, merchant and other displayed details. Offscreen controls can have empty inner text while their accessible names are populated. The first extraction initially missed these controls; the original saved first-batch DOM snapshot supplied all 60 names, without another query or backfilling later recommendations. Subsequent extraction used the accessible names directly. Snapshot text collapses spaces differently from the DOM attributes, so catalog names normalize whitespace. Original captured spacing is retained in occurrence text where available.

All records were captured before any new game-theoretic analysis. No agent selected a shortlist, ranked buyer utility or filtered these sets for completeness. No merchant landing-page verification or purchase occurred in this phase.

## Public projection

The fixed scenario excludes raw screenshots, whole-page DOM/accessibility captures, account/footer UI, ad-click links, opaque redirects and tracking parameters. Personalized nearby-distance numbers in product cards are replaced with `[distance removed]`. Relative delivery language and “also nearby” labels remain source claims, not verified fulfillment promises.

Catalog normalization preserves card text or the accessible product-card name, subject to that distance redaction. It collapses Google accessible-name whitespace and removes repeated, empty or decorative Bing image-alt strings. Extracted titles omit interface instructions and badges; ellipsized titles remain marked as truncated. USD is the currency interpretation of the observed dollar prices in this US environment. No currency conversion is performed.

For Bing main cards, the numeric `goid` already present in a product-details link is retained as a provider product reference. Google card controls did not expose equivalent public product landing links in this extraction. Merchant URLs are null rather than guessed or reconstructed from opaque ad redirects.

Repeated observations are grouped only when their complete normalized payloads match. No fuzzy product-name matching, price harmonization, cross-provider merging or guessed equivalence is applied. The immutable catalog contains 279 Bing records and 186 Google records; these are not necessarily 465 distinct physical products.

## Reuse

Use the saved JSON and checksums to reproduce the same recommendation universe offline. A later live recollection must receive a new version and preserve its own timestamps; it should not silently overwrite this snapshot. Any future analysis should reference this scenario version and manifest. Game conditions and analyses are intentionally absent from this release.
