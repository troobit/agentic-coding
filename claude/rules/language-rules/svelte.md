---
paths: **/*.svelte, **/*.svelte.ts, **/*.svelte.js
---

# Svelte 5 language rules

## Reactivity

- Attachments (`{@attach ...}`) and `$effect` bodies re-run whenever state
  READ inside them changes — and `count++` / `count += 1` counts as a read.
  Incrementing an invalidation counter inside an attachment therefore
  self-retriggers it: with the counter also bumped in cleanup, this loops
  until `effect_update_depth_exceeded` and permanently wedges the client
  scheduler (buttons and client-side navigation die; native scroll survives).
  Wrap such bumps in `untrack(() => counter++)`. Callbacks that fire outside
  tracked contexts (ResizeObserver, event listeners, timers) do not need it.
- Never gate an effect on a whole load-`data` prop object: SvelteKit hands
  over a fresh object on every `invalidateAll()`, and a plain-object prop is
  one reactive source — the effect fires on ANY reassignment. Gate on the
  specific values (a signature string or value-equal `$derived`) instead.
- A wedged-scheduler symptom profile — clicks ignored, `goto`/links dead,
  scrolling fine — means an exception was thrown during an earlier flush
  (often `effect_update_depth_exceeded`), not that the handler is wrong.
  Check the console before debugging the handler.

## SvelteKit

- Never export non-handler helpers from `+server.ts` / `+page.ts` files — the
  postbuild analysis rejects them and `pnpm build` fails (plain `check` does
  not catch it). Put shared helpers in `$lib`.

## Testing

- Vitest stubs CSS imports to an empty module **even with `?raw`**, and in the
  jsdom environment `import.meta.url` is not a `file:` URL. A test that needs a
  stylesheet's source text (e.g. asserting design-token values) must read it
  from disk with `node:fs` against `process.cwd()` (vitest sets cwd to the
  project root).

- On Node ≥ 22, vitest's jsdom environment has NO working Web Storage: Node's
  experimental `localStorage`/`sessionStorage` globals (lazy getters, undefined
  without `--localstorage-file`) shadow jsdom's, because vitest skips copying
  keys the Node global already owns — and vitest's `window` IS `globalThis`, so
  no jsdom Storage object is reachable regardless of the jsdom URL. Fix with a
  `setupFiles` entry that `Object.defineProperty`s an in-memory `Storage`
  implementation over both globals.

- Vitest with `environment: 'node'` compiles effects/attachments to SSR
  no-ops: client reactivity cannot be unit-tested there. Extract decisions
  into pure helpers for unit tests, and verify wiring in a real browser.
  A dependency-free harness that works: headless Chrome over CDP
  (`--headless=new --remote-debugging-port`, connect to
  `webSocketDebuggerUrl` with Node's global WebSocket, drive via
  `Runtime.evaluate`). Verify at a viewport where the feature actually
  renders — headless Chrome defaults to 800×600 and media-query-gated UI may
  simply be absent there. `Runtime.enable` replays the tab's console backlog;
  discard events for a settle period or stale errors look current.
