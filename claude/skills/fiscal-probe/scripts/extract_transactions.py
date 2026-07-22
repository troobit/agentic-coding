#!/usr/bin/env python3
"""Extract transactions from PDF bank/credit-card statements into a normalised CSV.

Usage: extract_transactions.py file1.pdf [file2.pdf ...] -o transactions.csv

Output columns: source_file, page, date (ISO), description, amount, balance, currency, sign
sign values: column (debit/credit column), +/- (explicit CR/DR or minus),
             inferred (from balance delta), cc-conv (credit-card convention), raw (unknown)
Auto-detects date format (DD/MM vs MM/DD) and currency per document.
Prints parse yield per file so the caller can judge quality.

Text extraction uses `pdftotext -layout` (poppler) because it preserves column
alignment; falls back to pdfplumber if poppler is unavailable.
"""
import argparse
import csv
import re
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------- amounts

AMOUNT_RE = re.compile(r"""
    (?P<neg>[-(])?\s*
    (?P<cur>[£$€])?\s*
    (?P<num>\d{1,3}(?:,\d{3})+\.\d{2}|\d+\.\d{2})
    \s*(?P<close>\))?
    \s*(?P<crdr>CR|DR|C|D)?$
""", re.VERBOSE)


def parse_amount(token: str):
    """Parse a monetary token -> (float, currency|None, explicit_sign|None)."""
    m = AMOUNT_RE.fullmatch(token.strip())
    if not m:
        return None
    val = float(m.group("num").replace(",", ""))
    sign = None
    if m.group("neg") or m.group("close"):
        val, sign = -val, "-"
    crdr = m.group("crdr")
    if crdr in ("DR", "D"):
        val, sign = -abs(val), "-"
    elif crdr in ("CR", "C"):
        val, sign = abs(val), "+"
    return val, m.group("cur"), sign


AMOUNT_SCAN_RE = re.compile(
    r"[-(]?\s?[£$€]?\s?(?:\d{1,3}(?:,\d{3})+\.\d{2}|\d+\.\d{2})\)?(?:\s?(?:CR|DR)\b)?")


def amounts_in_line(line):
    """Yield (start, end, parsed) for each amount token in a line."""
    for m in AMOUNT_SCAN_RE.finditer(line):
        parsed = parse_amount(m.group(0))
        if parsed:
            yield m.start(), m.end(), parsed


# ---------------------------------------------------------------- dates

MONTHS = {m.lower(): i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}

DATE_NUM_RE = re.compile(r"^(\d{1,2})[/\-.](\d{1,2})(?:[/\-.](\d{2,4}))?$")
DATE_TXT_RE = re.compile(r"^(\d{1,2})\s+([A-Za-z]{3,9})\.?\s*(\d{2,4})?$")
DATE_TXT_US_RE = re.compile(r"^([A-Za-z]{3,9})\.?\s+(\d{1,2}),?\s*(\d{2,4})?$")
DATE_ISO_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")

LEADING_DATE_RE = re.compile(
    r"^\s*(\d{4}-\d{2}-\d{2}"
    r"|\d{1,2}[/\-.]\d{1,2}(?:[/\-.]\d{2,4})?"
    r"|\d{1,2}\s+[A-Za-z]{3,9}\.?(?:\s+\d{2,4})?"
    r"|[A-Za-z]{3,9}\.?\s+\d{1,2},?(?:\s+\d{2,4})?)\s+")

# for format detection only: slash/dash-separated (a bare 15.99 must NOT match)
DETECT_DATE_RE = re.compile(
    r"\b\d{1,2}[/\-]\d{1,2}(?:[/\-]\d{2,4})?\b|\b\d{1,2}\.\d{1,2}\.\d{2,4}\b")


def detect_date_format(text):
    """Decide 'DMY' or 'MDY' from unambiguous dates (a component > 12).

    Returns (fmt, certain: bool). Defaults to DMY when nothing is decisive.
    """
    d_first = m_first = 0
    for t in DETECT_DATE_RE.findall(text):
        m = DATE_NUM_RE.match(t)
        if not m:
            continue
        a, b = int(m.group(1)), int(m.group(2))
        if a > 31 or b > 31:
            continue
        if a > 12 and b <= 12:
            d_first += 1
        elif b > 12 and a <= 12:
            m_first += 1
    if d_first and not m_first:
        return "DMY", True
    if m_first and not d_first:
        return "MDY", True
    if d_first or m_first:
        return ("DMY" if d_first >= m_first else "MDY"), False
    return "DMY", False


def _year4(y, fallback):
    if y is None:
        return fallback
    y = int(y)
    return y + 2000 if y < 100 else y


def normalise_date(token: str, fmt: str, default_year: int):
    """Date token -> ISO string or None."""
    token = token.strip().rstrip(",")
    m = DATE_ISO_RE.match(token)
    if m:
        return token
    m = DATE_NUM_RE.match(token)
    if m:
        a, b, y = int(m.group(1)), int(m.group(2)), m.group(3)
        d, mo = (a, b) if fmt == "DMY" else (b, a)
        if a > 12 >= b:
            d, mo = a, b
        elif b > 12 >= a:
            d, mo = b, a
        try:
            return datetime(_year4(y, default_year), mo, d).strftime("%Y-%m-%d")
        except ValueError:
            return None
    for rx, order in ((DATE_TXT_RE, "dm"), (DATE_TXT_US_RE, "md")):
        m = rx.match(token)
        if m:
            if order == "dm":
                d, mon, y = int(m.group(1)), m.group(2)[:3].lower(), m.group(3)
            else:
                mon, d, y = m.group(1)[:3].lower(), int(m.group(2)), m.group(3)
            if mon in MONTHS:
                try:
                    return datetime(_year4(y, default_year), MONTHS[mon], d
                                    ).strftime("%Y-%m-%d")
                except ValueError:
                    return None
    return None


def infer_default_year(text: str):
    years = [int(y) for y in re.findall(r"\b(20\d{2})\b", text)]
    return Counter(years).most_common(1)[0][0] if years else datetime.now().year


def detect_currency(text: str):
    """Explicit ISO code > country cues > unambiguous symbol. A bare '$' is
    NEVER trusted as a currency — it's ambiguous across AUD/NZD/SGD/USD."""
    for code in ("AUD", "NZD", "SGD", "GBP", "USD", "EUR", "CAD", "CHF"):
        if re.search(rf"\b{code}\b", text):
            return code
    up = text.upper()
    if (re.search(r"\bABN\s+\d{2}\s?\d{3}\s?\d{3}\s?\d{3}\b", up)
            or re.search(r"\bBSB\b", up)
            or re.search(r"\bPTY\s+LTD\b", up)
            or (re.search(r"\b(WESTPAC|ANZ|NAB|COMMONWEALTH BANK|BENDIGO|SUNCORP)\b", up)
                and re.search(r"\b(NSW|VIC|QLD|WA|SA|TAS|AUSTRALIA)\b", up))):
        return "AUD"
    if re.search(r"\bNZBN\b|\bNEW ZEALAND\b|\bKIWIBANK\b|\bAOTEAROA\b", up):
        return "NZD"
    if re.search(r"\bUEN\b|\bSINGAPORE\b|\b(DBS|OCBC|UOB)\s+BANK\b|\bPAYNOW\b", up):
        return "SGD"
    counts = Counter(c for c in text if c in "£€")
    if counts:
        return counts.most_common(1)[0][0]
    return "$?" if "$" in text else "?"


# ---------------------------------------------------------------- text extraction

def pdf_pages_text(path: Path):
    """Return list of page texts, layout-preserved. pdftotext primary."""
    if shutil.which("pdftotext"):
        out = subprocess.run(["pdftotext", "-layout", str(path), "-"],
                             capture_output=True, text=True)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.split("\f")
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            return [(p.extract_text(layout=True) or "") for p in pdf.pages]
    except ImportError:
        return []


# ---------------------------------------------------------------- line parsing

DEBIT_HEADER_RE = re.compile(r"paid\s*out|debits?\b|withdrawals?|money\s*out", re.I)
CREDIT_HEADER_RE = re.compile(r"paid\s*in|credits?\b|deposits?|money\s*in", re.I)
BALANCE_HEADER_RE = re.compile(r"\bbalance\b", re.I)
NON_TXN_RE = re.compile(
    r"opening\s+balance|closing\s+balance|balance\s+(brought|carried)\s+forward"
    r"|statement\s+(period|date)|balance\s+forward", re.I)


def find_columns(lines):
    """Find debit/credit/balance header spans from the first plausible header line."""
    for line in lines[:30]:
        dm = DEBIT_HEADER_RE.search(line)
        cm = CREDIT_HEADER_RE.search(line)
        if dm and cm:
            cols = {"debit": dm.span(), "credit": cm.span()}
            bm = BALANCE_HEADER_RE.search(line)
            if bm:
                cols["balance"] = bm.span()
            return cols
    return {}


def nearest_column(span, cols, tol=18):
    """Assign an amount span to the column whose right edge is closest."""
    best, best_d = None, tol + 1
    for name, (c0, c1) in cols.items():
        d = min(abs(span[1] - c1), abs(span[0] - c0))
        if d < best_d:
            best, best_d = name, d
    return best


def parse_file(path: Path):
    pages = pdf_pages_text(path)
    full_text = "\n".join(pages)
    if not full_text.strip():
        return [], {"error": "no text layer (scanned?) — see SKILL.md step 1",
                    "candidates": 0, "parsed": 0}
    default_year = infer_default_year(full_text)
    currency = detect_currency(full_text)
    fmt, certain = detect_date_format(full_text)
    if not certain and re.search(
            r"\b\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{2,4}\b"
            r"|\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{2,4}\b",
            full_text) and not DETECT_DATE_RE.search(full_text):
        certain = True  # dates are textual month names -- no DMY/MDY ambiguity

    rows, candidates, parsed_count = [], 0, 0
    prev_balance, has_columns = None, False
    for pageno, text in enumerate(pages, 1):
        lines = text.splitlines()
        cols = find_columns(lines)
        has_columns = has_columns or bool(cols)
        for line in lines:
            dm = LEADING_DATE_RE.match(line)
            if not dm:
                continue
            iso = normalise_date(dm.group(1), fmt, default_year)
            if not iso:
                continue
            amts = list(amounts_in_line(line))
            amts = [a for a in amts if a[0] >= dm.end()]
            is_non_txn = bool(NON_TXN_RE.search(line))
            if not is_non_txn:
                candidates += 1
            if not amts:
                continue
            if is_non_txn:
                # seed running balance from opening/closing balance lines
                prev_balance = amts[-1][2][0]
                continue
            desc = line[dm.end():amts[0][0]].strip()
            desc = LEADING_DATE_RE.sub("", desc + " ").strip()  # drop 2nd date col
            if not desc:
                continue

            amount, balance, sign = None, None, None
            if cols:
                for s, e, (val, _c, xsign) in amts:
                    col = nearest_column((s, e), cols)
                    if col == "balance":
                        balance = val
                    elif col == "debit":
                        amount, sign = -abs(val), "column"
                    elif col == "credit":
                        amount, sign = abs(val), "column"
                if amount is None:
                    amount = amts[0][2][0]
                    sign = amts[0][2][2] or "raw"
            else:
                val, _c, xsign = amts[0][2]
                amount, sign = val, xsign or "raw"
                if len(amts) >= 2:
                    balance = amts[-1][2][0]

            if sign == "raw" and balance is not None and prev_balance is not None:
                delta = round(balance - prev_balance, 2)
                if abs(abs(delta) - abs(amount)) < 0.01:
                    amount, sign = delta, "inferred"
            if balance is not None:
                prev_balance = balance

            parsed_count += 1
            rows.append({
                "source_file": path.name, "page": pageno, "date": iso,
                "description": re.sub(r"\s{2,}", " ", desc),
                "amount": amount, "balance": balance,
                "currency": currency, "sign": sign or "raw",
            })

    # Credit-card convention: no dr/cr columns, some rows explicitly CR (+),
    # remaining unmarked positives are charges -> negative.
    if not has_columns and any(r["sign"] == "+" for r in rows):
        for r in rows:
            if r["sign"] == "raw" and r["amount"] > 0:
                r["amount"], r["sign"] = -r["amount"], "cc-conv"

    for r in rows:
        r["amount"] = f"{r['amount']:.2f}"
        r["balance"] = f"{r['balance']:.2f}" if r["balance"] is not None else ""

    stats = {"candidates": candidates, "parsed": parsed_count, "date_format": fmt,
             "date_format_certain": certain, "currency": currency}
    return rows, stats


def dedupe(rows):
    """Drop duplicates of (date, amount, description) appearing in >1 file
    (overlapping statement periods). Same-file duplicates are kept."""
    first_file, out = {}, []
    for r in rows:
        key = (r["date"], r["amount"], re.sub(r"\W", "", r["description"]).upper())
        if key in first_file and first_file[key] != r["source_file"]:
            continue
        first_file.setdefault(key, r["source_file"])
        out.append(r)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdfs", nargs="+")
    ap.add_argument("-o", "--output", default="transactions.csv")
    ap.add_argument("--currency", action="append", default=[], metavar="FILE=CODE",
                    help="Override detected currency, e.g. --currency statement.pdf=AUD. "
                         "Use FILE=* rarely; ALL=CODE applies to every file.")
    args = ap.parse_args()
    overrides = dict(c.split("=", 1) for c in args.currency)

    all_rows = []
    for p in args.pdfs:
        path = Path(p)
        rows, stats = parse_file(path)
        cur_override = overrides.get(path.name) or overrides.get("ALL")
        if cur_override:
            for r in rows:
                r["currency"] = cur_override
            stats["currency"] = cur_override
        all_rows.extend(rows)
        if stats.get("error"):
            print(f"[WARN] {path.name}: {stats['error']}", file=sys.stderr)
            continue
        pct = 100 * stats["parsed"] / stats["candidates"] if stats["candidates"] else 0
        flag = "" if pct >= 80 else "  << LOW YIELD, verify manually (SKILL.md step 3)"
        amb = "" if stats["date_format_certain"] else " (AMBIGUOUS — defaulted, verify!)"
        print(f"{path.name}: {stats['parsed']}/{stats['candidates']} lines parsed "
              f"({pct:.0f}%), dates={stats['date_format']}{amb}, "
              f"currency={stats['currency']}{flag}")
        if stats["currency"] in ("?", "$?"):
            print(f"  [!] {path.name}: currency unresolved ('$' is ambiguous across "
                  f"AUD/NZD/SGD/USD). Re-run with --currency {path.name}=AUD (etc.)",
                  file=sys.stderr)

    before = len(all_rows)
    all_rows = dedupe(all_rows)
    all_rows.sort(key=lambda r: (r["date"], r["source_file"], r["page"]))
    if before != len(all_rows):
        print(f"Deduplicated {before - len(all_rows)} overlapping rows across files")

    with open(args.output, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["source_file", "page", "date", "description",
                                          "amount", "balance", "currency", "sign"])
        w.writeheader()
        w.writerows(all_rows)
    print(f"Wrote {len(all_rows)} transactions -> {args.output}")


if __name__ == "__main__":
    main()
