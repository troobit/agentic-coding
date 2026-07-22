# Fiscal Probe JSON contract

`analyze.py --json out.json` emits the machine-readable payload for the
fiscal-probe web frontend. This file is the contract: update it whenever the
payload shape changes.

All amounts are floats in the transaction's own currency (never converted or
merged across currencies). Transaction `id`s are indices into `transactions`
for **this run only** — they change when filters change, so persist the
`(source_file, page, date, description, amount)` tuple, not the id, if you
need a durable key.

```jsonc
{
  "period": ["2026-04-02", "2026-06-27"],   // first/last date after filtering
  "filters": {                               // the filters this payload was built with
    "from": null, "to": null, "type": null,
    "merchant": null, "min": null, "max": null, "sort": "date"
  },
  "transactions": [
    {
      "id": 0,                               // index in this array
      "source_file": "westpac_personal.pdf", // claim reference: file...
      "page": 1,                             // ...and page (int, 1-based)
      "date": "2026-04-02",                  // ISO
      "description": "WITHDRAWAL-ATM WBC PITT ST SYDNEY NS",
      "amount": -800.0,                      // negative = money out
      "currency": "AUD",
      "sign": "inferred",                    // column | + | - | inferred | cc-conv | raw
      "type": "cash"                         // cash | transfer | card | direct_debit | deposit | payment | fee | cheque
    }
  ],
  "groups": {                                // similar-transaction groups
    "CASH WITHDRAWAL BRANCH PARRAMATTA": [8, 21, 30]   // transaction ids
  },
  "recurring": [
    { "name": "BY AUTHORITY TO AGL ENERGY", "interval_days": 30.0,
      "amount": 214.3, "count": 3, "ids": [9, 20, 31] }
  ],
  "transfers": [                             // cross-account pairs (exact amount, ±3 days)
    { "amount": 15000.0, "from": "meridian_business.pdf",
      "to": "westpac_personal.pdf", "dates": ["2026-04-03", "2026-04-04"],
      "ids": [1, 3] }
  ]
}
```

Frontend rules that follow from the brief use case:

- Every rendered claim (transaction, group total, recurring row, transfer)
  must display its source reference, derived from `source_file` + `page` of
  the underlying transaction ids. Nothing renders without a reference.
- `sign: "inferred"` rows should be visually flagged — the sign came from a
  balance delta, not an explicit debit/credit marker.
- Totals shown in the UI must be recomputed from `transactions`, not carried
  from the markdown report, so the displayed figures always re-derive from
  the referenced rows.
