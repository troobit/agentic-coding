#!/usr/bin/env python3
"""Analyse a transactions CSV: spending insight, similar-transaction groups,
recurring payments, cross-account transfers. Emits markdown (default) or txt.

Usage: analyze.py transactions.csv -o report.md [filters]
"""
import argparse
import csv
import re
import statistics
from collections import defaultdict
from datetime import datetime
from difflib import SequenceMatcher

# ---- tunables (see SKILL.md "How similarity works") ----
FUZZY_THRESHOLD = 0.85       # merge merchant groups above this ratio
RECUR_MIN_TXNS = 3
RECUR_INTERVAL_RANGE = (6, 95)   # days: weekly .. quarterly-ish
RECUR_INTERVAL_CV = 0.35
RECUR_AMOUNT_SPREAD = 0.25       # max spread as fraction of median amount
TRANSFER_WINDOW_DAYS = 3

NOISE_TOKENS = {
    "POS", "DD", "SO", "VIS", "CRD", "BGC", "FPI", "FPO", "DEB", "CR", "DR",
    "TFR", "ATM", "CHQ", "BP", "CARD", "PAYMENT", "PURCHASE", "DEBIT",
    "CREDIT", "CONTACTLESS", "ONLINE", "REF", "LTD", "LIMITED", "INC", "LLC",
    "PLC", "COM", "CO", "UK", "GB", "US", "WWW",
}


# Transaction-type classification (AU/NZ/SG/UK/US rails). Order matters:
# first match wins. Tunable -- extend patterns as new statement styles appear.
TYPE_RULES = [
    ("cash", r"\bATM\b|CASH\s*W/?D|CASH\s+WITHDRAWAL|WITHDRAWAL[- ]?ATM"
             r"|WITHDRAWAL[- ]?BRANCH|BRANCH\s+CASH|CASH\s+ADVANCE|CASH\s+OUT"),
    ("transfer", r"\bTFR\b|TRANSFER|TELEGRAPHIC|\bTT\b|\bIMT\b|\bRTGS\b"),
    ("direct_debit", r"\bDD\b|DIRECT\s+DEBIT|PAYMENT\s+BY\s+AUTHORITY|\bSO\b"
                     r"|STANDING\s+ORDER|\bGIRO\b|AUTOPAY"),
    ("card", r"EFTPOS|\bPOS\b|\bCRD\b|\bVIS\b|VISA|MASTERCARD|PAYWAVE"
             r"|CARD\s+PURCHASE|DEBIT\s+CARD"),
    ("fee", r"\bFEE\b|SERVICE\s+CHARGE|ACCOUNT\s+SERVICING|BANK\s+CHARGES"
            r"|\bINTEREST\b|GOVT\s+"),
    ("cheque", r"\bCHQ\b|CHEQUE|CHECK\s+\d"),
    ("deposit_in", r"DEPOSIT|SALARY|\bBGC\b|INVOICE\s+PAYMENT\s+RCVD|PAYNOW"
                   r"|OSKO\s+PAYMENT|\bFPI\b|PAY/SALARY"),
]
_TYPE_RES = [(t, re.compile(p, re.I)) for t, p in TYPE_RULES]


def classify(desc: str, amount: float) -> str:
    for t, rx in _TYPE_RES:
        if rx.search(desc):
            if t == "deposit_in":
                return "deposit" if amount > 0 else "payment"
            return t
    return "deposit" if amount > 0 else "payment"


def normalise_merchant(desc: str) -> str:
    s = desc.upper()
    s = re.sub(r"[*#/\\]", " ", s)
    s = re.sub(r"\b\d{2}[A-Z]{3}\d{0,2}\b", " ", s)      # embedded dates 03APR
    s = re.sub(r"\b\d{4,}\b", " ", s)                     # long refs / card nums
    s = re.sub(r"[^A-Z0-9& ]", " ", s)
    toks = [t for t in s.split() if t not in NOISE_TOKENS and not t.isdigit()]
    result = " ".join(toks)
    if len(result) < 4:  # over-stripped (e.g. "TFR TO CREDIT CARD SO" -> "TO")
        toks = [t for t in s.split() if not t.isdigit()]
        result = " ".join(toks)
    return result or desc.upper().strip()


def load(path):
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["amount"] = float(r["amount"])
        r["page"] = int(r["page"])
        r["_d"] = datetime.strptime(r["date"], "%Y-%m-%d")
        r["_m"] = normalise_merchant(r["description"])
        r["type"] = classify(r["description"], r["amount"])
    return rows


def group_merchants(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[r["_m"]].append(r)
    # fuzzy-merge group names
    names = sorted(groups, key=lambda n: -len(groups[n]))
    merged, canon = {}, []
    for n in names:
        hit = next((c for c in canon
                    if SequenceMatcher(None, n, c).ratio() >= FUZZY_THRESHOLD), None)
        if hit:
            groups[hit].extend(groups.pop(n))
            merged[n] = hit
        else:
            canon.append(n)
    return groups


def recurring(groups):
    out = []
    for name, txns in groups.items():
        if len(txns) < RECUR_MIN_TXNS:
            continue
        txns = sorted(txns, key=lambda r: r["_d"])
        gaps = [(b["_d"] - a["_d"]).days for a, b in zip(txns, txns[1:])]
        gaps = [g for g in gaps if g > 0]
        if len(gaps) < RECUR_MIN_TXNS - 1:
            continue
        med = statistics.median(gaps)
        if not (RECUR_INTERVAL_RANGE[0] <= med <= RECUR_INTERVAL_RANGE[1]):
            continue
        cv = (statistics.pstdev(gaps) / statistics.mean(gaps)) if statistics.mean(gaps) else 9
        amts = [abs(t["amount"]) for t in txns]
        amed = statistics.median(amts)
        spread = (max(amts) - min(amts)) / amed if amed else 9
        if cv <= RECUR_INTERVAL_CV and spread <= RECUR_AMOUNT_SPREAD:
            out.append({"name": name, "txns": txns, "interval": med,
                        "amount": amed, "spread": spread})
    return sorted(out, key=lambda g: -abs(g["amount"]))


def transfers(rows):
    pairs, used = [], set()
    by_amt = defaultdict(list)
    for i, r in enumerate(rows):
        by_amt[round(abs(r["amount"]), 2)].append(i)
    for amt, idxs in by_amt.items():
        for i in idxs:
            if i in used:
                continue
            for j in idxs:
                if j <= i or j in used:
                    continue
                a, b = rows[i], rows[j]
                if (a["source_file"] != b["source_file"]
                        and a["amount"] * b["amount"] < 0
                        and abs((a["_d"] - b["_d"]).days) <= TRANSFER_WINDOW_DAYS):
                    pairs.append((a, b))
                    used.update((i, j))
                    break
    return pairs


def link(r):
    return f"[{r['source_file']} p.{r['page']}]"


CUR_DISPLAY = {"AUD": "A$", "NZD": "NZ$", "SGD": "S$", "USD": "$",
               "GBP": "£", "EUR": "€", "$?": "$"}


def fmt_amt(v, cur):
    c = cur if cur in "£$€" else CUR_DISPLAY.get(cur, "")
    return f"{c}{v:,.2f}" if v >= 0 else f"-{c}{abs(v):,.2f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("-o", "--output", default="report.md")
    ap.add_argument("--from", dest="dfrom")
    ap.add_argument("--to", dest="dto")
    ap.add_argument("--merchant")
    ap.add_argument("--min", type=float)
    ap.add_argument("--max", type=float)
    ap.add_argument("--type", help="Comma list: cash,transfer,card,direct_debit,"
                    "deposit,payment,fee,cheque")
    ap.add_argument("--sort", default="date",
                    help="Listing order, comma multi-key: date,value,-value,-date "
                         "(value = absolute amount; '-' prefix = descending)")
    ap.add_argument("--list", action="store_true", dest="listing",
                    help="Force the transaction listing section")
    ap.add_argument("--json", dest="json_out", metavar="FILE",
                    help="Also write machine-readable JSON (for UIs/automation)")
    ap.add_argument("--recurring-only", action="store_true")
    ap.add_argument("--transfers-only", action="store_true")
    ap.add_argument("--txt", action="store_true")
    ap.add_argument("--top", type=int, default=15)
    args = ap.parse_args()

    rows = load(args.csv)
    if args.dfrom:
        rows = [r for r in rows if r["date"] >= args.dfrom]
    if args.dto:
        rows = [r for r in rows if r["date"] <= args.dto]
    if args.min is not None:
        rows = [r for r in rows if abs(r["amount"]) >= args.min]
    if args.max is not None:
        rows = [r for r in rows if abs(r["amount"]) <= args.max]
    if args.merchant:
        q = normalise_merchant(args.merchant)
        rows = [r for r in rows if q in r["_m"]
                or SequenceMatcher(None, q, r["_m"]).ratio() >= 0.7]
    if args.type:
        wanted = {t.strip().lower() for t in args.type.split(",")}
        rows = [r for r in rows if r["type"] in wanted]
    if not rows:
        print("No transactions after filtering.")
        return

    rows.sort(key=lambda r: r["date"])
    for i, r in enumerate(rows):
        r["_id"] = i  # stable id within this run; JSON consumers key on it
    groups = group_merchants(rows)
    recs = recurring(groups)
    xfers = transfers(rows)
    currencies = sorted({r["currency"] for r in rows})

    H2, H3, B = ("## ", "### ", "**") if not args.txt else ("== ", "-- ", "")
    L = []
    L.append(("# " if not args.txt else "") + "Fiscal Probe Report")
    L.append("")
    L.append(f"{H2}Summary")
    L.append(f"Period: {rows[0]['date']} to {rows[-1]['date']}  |  "
             f"{len(rows)} transactions  |  sources: "
             f"{', '.join(sorted({r['source_file'] for r in rows}))}")
    for cur in currencies:
        cr = [r for r in rows if r["currency"] == cur]
        tin = sum(r["amount"] for r in cr if r["amount"] > 0)
        tout = sum(r["amount"] for r in cr if r["amount"] < 0)
        L.append(f"- {cur}: in {fmt_amt(tin, cur)}, out {fmt_amt(tout, cur)}, "
                 f"net {fmt_amt(tin + tout, cur)}")
    inferred = sum(1 for r in rows if r["sign"] == "inferred")
    if inferred:
        L.append(f"- Note: {inferred} amounts have balance-inferred signs")
    L.append("")

    if not (args.recurring_only or args.transfers_only):
        L.append(f"{H2}Monthly flow")
        for cur in currencies:
            if len(currencies) > 1:
                L.append(f"{H3}Currency: {cur}")
            months = defaultdict(lambda: defaultdict(float))
            for r in rows:
                if r["currency"] != cur:
                    continue
                months[r["date"][:7]]["in" if r["amount"] > 0 else "out"] += r["amount"]
            if not args.txt:
                L.append("| Month | In | Out | Net |")
                L.append("|---|---:|---:|---:|")
            for m in sorted(months):
                i, o = months[m]["in"], months[m]["out"]
                L.append(f"| {m} | {fmt_amt(i, cur)} | {fmt_amt(o, cur)} | {fmt_amt(i+o, cur)} |"
                         if not args.txt else
                         f"{m}: in {fmt_amt(i, cur)}, out {fmt_amt(o, cur)}, "
                         f"net {fmt_amt(i+o, cur)}")
            L.append("")

        L.append(f"{H2}Top merchant groups (similar transactions)")
        ranked = sorted(groups.items(),
                        key=lambda kv: -sum(abs(t["amount"]) for t in kv[1] if t["amount"] < 0))
        for name, txns in ranked[: args.top]:
            spend = sum(t["amount"] for t in txns if t["amount"] < 0)
            if spend == 0:
                continue
            cur = txns[0]["currency"]
            L.append(f"{H3}{name.title()} — {len(txns)} txns, total {fmt_amt(spend, cur)}")
            for t in sorted(txns, key=lambda t: t["date"]):
                L.append(f"- {t['date']}  {fmt_amt(t['amount'], cur)}  "
                         f"{t['description']}  {link(t)}")
            L.append("")

    if not args.transfers_only:
        L.append(f"{H2}Recurring payments")
        if not recs:
            L.append("None detected.")
        for g in recs:
            cur = g["txns"][0]["currency"]
            L.append(f"- {B}{g['name'].title()}{B}: ~every {g['interval']:.0f} days, "
                     f"~{fmt_amt(g['amount'], cur)} × {len(g['txns'])} "
                     f"({g['txns'][0]['date']} → {g['txns'][-1]['date']}) "
                     f"{' '.join(link(t) for t in g['txns'][:3])}"
                     + (" ..." if len(g["txns"]) > 3 else ""))
        L.append("")

    if not args.recurring_only:
        L.append(f"{H2}Cross-account transfers")
        if not xfers:
            L.append("None detected." if len({r['source_file'] for r in rows}) > 1
                     else "Single source file — transfer matching needs ≥2 accounts.")
        for a, b in xfers:
            out_r, in_r = (a, b) if a["amount"] < 0 else (b, a)
            cur = out_r["currency"]
            L.append(f"- {fmt_amt(abs(out_r['amount']), cur)}: "
                     f"{out_r['source_file']} ({out_r['date']}) → "
                     f"{in_r['source_file']} ({in_r['date']})  "
                     f"{link(out_r)} {link(in_r)}")
        L.append("")

    show_listing = args.listing or args.type or args.sort != "date" or args.merchant
    if show_listing and not (args.recurring_only or args.transfers_only):
        keys = [k.strip() for k in args.sort.split(",")]

        def sort_key(r):
            out = []
            for k in keys:
                desc_order = k.startswith("-")
                k2 = k.lstrip("-")
                v = abs(r["amount"]) if k2 == "value" else r["date"]
                if desc_order:
                    v = -v if k2 == "value" else "".join(
                        chr(255 - ord(c)) for c in v)
                out.append(v)
            return tuple(out)

        listed = sorted(rows, key=sort_key)
        L.append(f"{H2}Transaction listing"
                 + (f" (type: {args.type})" if args.type else "")
                 + (f" (sort: {args.sort})" if args.sort != "date" else ""))
        if not args.txt:
            L.append("| Date | Type | Description | Amount | Source |")
            L.append("|---|---|---|---:|---|")
        for r in listed:
            cur = r["currency"]
            L.append(f"| {r['date']} | {r['type']} | {r['description']} | "
                     f"{fmt_amt(r['amount'], cur)} | {link(r)} |"
                     if not args.txt else
                     f"{r['date']}  {r['type']:<12} {fmt_amt(r['amount'], cur):>14}  "
                     f"{r['description']}  {link(r)}")
        L.append("")

    if args.json_out:
        import json
        payload = {
            "period": [rows[0]["date"], rows[-1]["date"]],
            "filters": {"from": args.dfrom, "to": args.dto, "type": args.type,
                        "merchant": args.merchant, "min": args.min, "max": args.max,
                        "sort": args.sort},
            "transactions": [
                {"id": r["_id"],
                 **{k: r[k] for k in ("source_file", "page", "date", "description",
                                      "amount", "currency", "sign", "type")}}
                for r in rows],
            "groups": {name: [t["_id"] for t in txns]
                       for name, txns in groups.items()},
            "recurring": [{"name": g["name"], "interval_days": g["interval"],
                           "amount": g["amount"], "count": len(g["txns"]),
                           "ids": [t["_id"] for t in g["txns"]]}
                          for g in recs],
            "transfers": [
                {"amount": abs(a["amount"]), "from": a["source_file"] if a["amount"] < 0 else b["source_file"],
                 "to": b["source_file"] if a["amount"] < 0 else a["source_file"],
                 "dates": [a["date"], b["date"]],
                 "ids": [a["_id"], b["_id"]]}
                for a, b in xfers],
        }
        with open(args.json_out, "w") as jf:
            json.dump(payload, jf, indent=1, default=str)

    with open(args.output, "w") as f:
        f.write("\n".join(L) + "\n")
    print(f"Wrote report -> {args.output} "
          f"({len(rows)} txns, {len(groups)} groups, {len(recs)} recurring, "
          f"{len(xfers)} transfer pairs)")


if __name__ == "__main__":
    main()
