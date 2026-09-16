# UI/UX Guide

A cross-repository reference for how interfaces here should behave. The Swift peer of this
file is [`../arjen-style-guide.md`](../arjen-style-guide.md); this one governs UI/UX, and
applies to spadre, rtob and whatever comes after.

Everything below is **derived**. Each principle is someone's reading of something Ronan
actually said, and every one of them cites the observation it rests on. If a principle looks
wrong, open its evidence and check — the verbatim comment is in there, and the verbatim
comment is the thing that cannot be wrong. A principle with no evidence is not a principle
and does not belong in this file.

Read it by **concern** — the part of the interface you are about to change. The vocabulary is
in [`concerns.md`](concerns.md); concerns with nothing recorded yet are not listed here.

## Principle status

| Status | Meaning |
|---|---|
| `affirmed` | He liked it. Do not break this. |
| `defect` | He said it is wrong. Wants fixing. |
| `proposed` | Derived from thin evidence, or from one comment that could read more than one way. Treat as a prompt to ask, not a rule to apply. |
| `retired` | Superseded or withdrawn. Kept, with the reason, because a reversal is evidence too. |

Evidence is variant-specific and the preference is not: a comment left on variant B is
evidence about variant B, but the rule it implies travels. Both are recorded — the principle
states the rule, the evidence names the variant.

---

## caret-and-selection

### UX-001 — Placing the caret is a thumb-sized action

**Status:** `affirmed` · **Also:** `touch-targets`

Putting the caret somewhere in the text must be doable with a thumb tap, at thumb precision.
Variant B achieves this and he called it out unprompted, which makes it the thing to carry
forward rather than rediscover. Do not regress to a target that needs a fingertip or a mouse.

**Evidence:** [`2026-09-15-59b0939f0c47`](observations/2026-09-15-59b0939f0c47.md) — Gratin,
variant B, 2026-09-15: _"The thumb tap for caret here is good…"_

### UX-002 — Whatever marks a position in text sits on the vertical centre of the line it refers to

**Status:** `defect` · **Also:** `layout-and-alignment`

The same comment that praised the tap reported the alignment as wrong: the element was not
vertically centred on the text it refers to. The rule is the general one — a caret handle, a
selection marker or the affordance that represents a position in text aligns to the vertical
middle of its line, so the thing you tapped and the thing you meant agree.

Which element is off-centre is **not established**; the observation records why, and that
uncertainty is not resolved here. Confirm on variant B before changing anything.

**Evidence:** [`2026-09-15-59b0939f0c47`](observations/2026-09-15-59b0939f0c47.md) — Gratin,
variant B, 2026-09-15: _"…but vertically not in the middle of the text to which it refers."_

---

## touch-targets

No principle rests on this concern alone yet. `UX-001` is tagged to it; see
`caret-and-selection` above.

## layout-and-alignment

No principle rests on this concern alone yet. `UX-002` is tagged to it; see
`caret-and-selection` above.
