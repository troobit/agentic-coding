---
name: sendit
description: Copy the active feature's spec documents from specs/{feature}/ into the user's Prism iCloud review folder (replacing same-named files) and close out the session. Use when a starwave approval gate asks "do the requirements/design/tasks look good?" and the user wants to review the documents in Prism, or whenever the user says "/sendit", "send it", "ship the spec to Prism", or "send these to review".
---

# Sendit — ship spec docs to Prism and close out

`/sendit` is the review-handoff action for the starwave workflow. The starwave reviewer is often **non-technical** and reviews markdown comfortably in the **Prism** app on their phone or iPad, not in a terminal. So instead of expecting an in-session "looks good", `/sendit` copies the current spec documents into the user's Prism iCloud folder and ends the session. The user reads the docs at their leisure, then runs `/nextup` next session — with no change requests, that next run counts as approval and the work continues; with change requests, they are applied first.

It does exactly two things:

1. Copies the active feature's `*.md` files into the Prism review folder, replacing any same-named files.
2. Closes out the session with a plain-English message — which docs went where, plus any loose ends — and stops.

It is the **default action** offered at every starwave approval gate ("Do the requirements look good?", "Does the design look good?", "Do the tasks look good?", "Does this smolspec look good?").

## The Prism folder

The target is the user's flat Prism review folder:

```
$HOME/Library/Mobile Documents/com~apple~CloudDocs/Prism Markdown/
```

Files are copied in **as is** — no per-feature subfolder, no name prefix. Only one set of spec docs ever lives there at a time, so a same-name file from a new feature simply replaces the old one. The long-lived versions stay in the repo under `specs/{feature}/`; Prism is a throwaway review surface.

## What `/sendit` does each run

### 1. Identify the active feature

Usually `/sendit` is invoked from inside a live starwave session, so the feature folder is already known — use it. If invoked standalone, resolve the feature the same way `/nextup` does, in priority order:

1. An explicit `specs/<name>/` reference in the conversation or the `nextup.md` user zone.
2. The current branch (`git rev-parse --abbrev-ref HEAD`), mapped to an existing `specs/<name>` folder (strip any `specs/` or `T-<n>/` prefix).

If neither resolves, ask the user in plain English which spec to send rather than guessing.

### 2. Copy the spec docs into Prism

Copy every markdown file in the feature folder, overwriting same-named files. Create the Prism folder if it is missing.

```bash
PRISM="$HOME/Library/Mobile Documents/com~apple~CloudDocs/Prism Markdown"
mkdir -p "$PRISM"
cp specs/{feature}/*.md "$PRISM/"
```

Confirm which files were copied. If the folder has no `.md` files, stop and say so — there is nothing to send.

### 3. Close out the session

Tell the user, in plain English: which feature's docs went to Prism, that the session is complete, and that they can review in Prism and run `/nextup` when they are ready — continuing without change requests counts as approving the docs. Include any loose ends in the same message: anything flagged during the session but never captured ("worth a follow-up", "separate ticket", "worth a regression test") gets a line here so it doesn't evaporate when the session ends. Then **stop** — do not continue the starwave phase, do not ask for inline approval, do not invoke any other skill.

A skill cannot quit the host application, so do not run any command that tries to kill the session. "Closing out" means finishing cleanly and ending the turn here.

## Hard rules

- Copy files **as is** — no subfolder, no prefix, no edits to the content.
- Replace same-named files in Prism; do not delete differently-named leftovers and do not wipe the folder.
- You touch only the Prism folder. You never write under `specs/` and never write `nextup.md`.
- Never proceed past the close-out. One run = copy, close out, stop.
