# Local next-task decisions

## Quick decisions

| Decision | Rationale |
| --- | --- |
| Use Codex's native LM Studio provider | The installed CLI supports local execution and discovers the existing skills; a live call to `8-bit` succeeded. |
| Start a fresh session after each selected group | The task ledger carries progress across sessions without accumulating the whole conversation in the model context. |
| Leave commits and phase reviews to the caller | The requested loop exposes the local model iteratively to tasks; it does not need make-it-so's delegation and release bookkeeping. |
| Use the checkout's skill manifests explicitly | A small local model gets concrete instructions even if its skill discovery differs from the active desktop session. |
