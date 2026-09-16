# UI concerns

The corpus is indexed by **concern** — the part of the interface a comment is about — not by
the document the comment happens to sit on. A comment left on line 18 of a review document
may be about a caret handle; the document is provenance, the concern is the index. See
`specs/ui-ux-corpus/decision_log.md`, Decision 3.

The vocabulary is **closed**. Use a slug from this list in an observation's `concerns:` field
and in `ui-ux-guide.md`. A comment may carry several — multi-membership is true of the data,
so it is not forced down to one.

## Adding a term

Add it here, with its scope and its nearest neighbour, in the same commit as the observation
that needed it. Do not invent a slug in an observation and file the definition later; that is
how a closed vocabulary becomes a tag soup. Do not add a term for a single observation that
an existing term covers adequately.

## The vocabulary

| Slug | Scope | Not this |
|---|---|---|
| `touch-targets` | Size and reachability of anything you tap or click: hit area, thumb zones, spacing between adjacent targets. | Where a control sits relative to other content — `layout-and-alignment`. |
| `caret-and-selection` | The text caret, selection handles, selection toolbars, and the act of picking a range of text. | The comment you create from a selection — `commenting-flow`. |
| `scrolling` | Scroll behaviour and position: momentum, restore-on-return, sticky regions, scroll-linked effects, overscroll. | Which chrome stays on screen while you scroll — `navigation-and-chrome`. |
| `navigation-and-chrome` | Persistent interface furniture and how you move between places: top bars, rails, locators, tab strips, back behaviour. | The visual weight of that furniture — `density-and-sizing`. |
| `commenting-flow` | Creating, reading, replying to, resolving and deleting a comment. spadre's core loop. | The button you press to start one, considered as a target — `touch-targets`. |
| `layout-and-alignment` | Where things sit relative to each other: centring, gutters, margins, alignment to the content they refer to. | How much space the layout gives overall — `density-and-sizing`. |
| `typography-and-measure` | Type scale, line length, line height, weight, wrapping and hyphenation. | The colour of the text — `colour-and-contrast`. |
| `density-and-sizing` | How large controls and content are and how tightly they are packed. | Whether a target is reachable at that size — `touch-targets`. |
| `colour-and-contrast` | Palette, contrast ratios, light and dark treatment, the meaning carried by a colour. | Whether a state change is noticed — `motion-and-feedback`. |
| `motion-and-feedback` | Transitions, animation, loading and pending states, and anything that tells you something happened. | The words used to tell you — `content-and-wording`. |
| `responsive-and-viewport` | Phone versus desktop widths, breakpoints, safe areas, keyboard avoidance, orientation. | A layout that is wrong at every width — `layout-and-alignment`. |
| `content-and-wording` | Labels, microcopy, empty states, error text, the names things are given. | The document being reviewed — that is provenance, not a concern. |
