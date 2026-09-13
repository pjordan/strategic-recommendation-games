# Pre-execution schema failure

The service rejected the recommender request with `invalid_json_schema`: `uniqueItems` was not permitted in the response schema. No recommender choice or buyer turn occurred. The original inputs, source/schema snapshots and failed manifests are preserved. The next attempt removes that schema keyword; local record-ID uniqueness checks remain enforced. The agent prompts and game conditions do not change.
