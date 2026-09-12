"""Load or validate the fixed scenario. Uses only Python's standard library."""
import argparse
import hashlib
import json
import re
from collections import Counter
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "scenarios" / "scenario-1"

def read(path):
    return json.loads(path.read_text())

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()

def load_context(role="recommender", root=ROOT):
    """Separate actor views; this API is not a filesystem security boundary."""
    if role not in ("buyer", "recommender"):
        raise ValueError("role must be buyer or recommender")
    result = {"public_context": read(root / "public_context.json")}
    if role == "buyer":
        result["private_user_preferences"] = read(root / "private/user_preferences.json")
    return result

def load_records(provider, root=ROOT):
    if provider not in ("bing", "google"):
        raise ValueError("Unknown recommendation set")
    return read(root / "recommendations" / (provider + ".json"))["records"]

def check(condition, message):
    if not condition:
        raise ValueError(message)

def validate_dataset(data):
    records = data["records"]
    ids = {r["record_id"] for r in records}
    check(len(ids) == len(records), "Duplicate record IDs")
    for r in records:
        payload = {k:v for k,v in r.items() if k not in ("record_id", "record_sha256")}
        check(digest(payload) == r["record_sha256"], "Record hash mismatch")
        check(r["record_id"] == data["provider"] + "-" + r["record_sha256"][:20], "Record ID mismatch")
        check(r["provider"] == data["provider"], "Provider mismatch")
        p = r["displayed_price_cents"]
        check(p is None or type(p) is int and p >= 0, "Invalid price")
        if p is not None:
            text = r["displayed_price_text"]
            check(re.fullmatch(r"\$[\d,]+(?:\.\d{1,2})?", text) is not None, "Invalid price text")
            check(int(Decimal(text[1:].replace(",", "")) * 100) == p, "Price amount mismatch")
            check(text in r["card_text"], "Displayed price absent from source text")
        check(r["product_verification"] == "not_adjudicated", "Scenario accidentally includes product adjudication")
    by_batch = Counter(o["batch"] for o in data["occurrences"])
    section_ranks = {}
    for o in data["occurrences"]:
        check(o["record_id"] in ids, "Occurrence refers to missing record")
        section_ranks.setdefault((o["batch"], o["source_section"]), []).append(o["rank_within_section_and_batch"])
    for ranks in section_ranks.values():
        check(ranks == list(range(1, len(ranks)+1)), "Source section ranks are not consecutive")
    for b in data["batches"]:
        check(by_batch[b["batch"]] == b["observed_cards"], "Batch count mismatch")
        check(b["main_cards"] + b["sponsored_cards"] == b["observed_cards"], "Section count mismatch")
    if data["provider"] == "bing":
        ranks = [o["provider_main_result_rank"] for o in data["occurrences"] if o["source_section"] == "featured"]
        check(ranks == list(range(1, 178)), "Bing main pages do not cover 1–177")
    return {"provider": data["provider"], "batches": len(data["batches"]), "records": len(records), "main_records": sum(not r["sponsored"] for r in records), "sponsored_records": sum(r["sponsored"] for r in records), "occurrences": len(data["occurrences"])}

def validate(root=ROOT):
    for line in (root / "manifest.sha256").read_text().splitlines():
        expected, relative = line.split("  ", 1)
        path = (root / relative).resolve()
        check(path.is_relative_to(root.resolve()), "Manifest path escapes scenario")
        check(hashlib.sha256(path.read_bytes()).hexdigest() == expected, "File checksum mismatch: " + relative)
    manifest = read(root / "scenario.json")
    summaries = [validate_dataset(read(root / "recommendations" / (provider + ".json"))) for provider in ("bing", "google")]
    check(manifest["analyses"] == [], "This release must contain no analyses")
    check("private_user_preferences" not in load_context("recommender", root), "Default context includes private preferences")
    for file in root.rglob("*.json"):
        text = file.read_text()
        for pattern in (r"/Users/", r"/home/", r"bing\.com/(?:aclick|ck/)", r"(?:fclid|rlid|gclid|msclkid|originIGUID)=", r"google\.com/(?:aclk|goto)", r"From your IP address", r"Nearby,\s*\d+\s*mi", r"Bearer\s+\S+"):
            check(re.search(pattern, text, re.I) is None, "Publication-screen pattern matched in " + file.name)
    return summaries

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    contexts = sub.add_parser("context")
    contexts.add_argument("--role", choices=("buyer", "recommender"), default="recommender")
    records = sub.add_parser("records")
    records.add_argument("--provider", choices=("bing", "google"), required=True)
    args = parser.parse_args()
    if args.command == "validate":
        result = validate()
    elif args.command == "context":
        result = load_context(args.role)
    else:
        result = load_records(args.provider)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
