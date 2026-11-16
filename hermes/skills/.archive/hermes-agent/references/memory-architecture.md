# Hermes Memory Architecture — Where Each "Memory" Actually Lives

When the user asks "where is my memory stored?" or "what gets injected into your context?", **do not guess from filenames in `~/.hermes/`**. Multiple `.db` files exist there (`memory_store.db`, `state.db`, `kanban.db`) and their names are misleading. Read this reference before answering, then verify the specific paths with `ls`/`search_files`.

## The four memory layers (and which one is auto-injected)

| Layer | Real storage | Auto-injected each turn? | Tool to access |
|:---|:---|:---:|:---|
| **Curated memory** (memory + user) | `$HERMES_HOME/memories/MEMORY.md` + `USER.md` — **plain text files** | ✅ **Yes**, full text | `memory` tool |
| **External memory provider** (e.g. holographic / fact_store) | `$HERMES_HOME/memory_store.db` (SQLite) or provider-specific path | ❌ No — only `system_prompt_block()` static text + on-demand `prefetch()` | `fact_store` (or provider's tool) |
| **Session transcripts** | `$HERMES_HOME/sessions/` (SQLite per session, FTS5) | ❌ No | `session_search` |
| **Skills** | `$HERMES_HOME/skills/<category>/<name>/SKILL.md` | ❌ No — only description lines pre-scanned | `skill_view` |

`state.db` and `kanban.db` are unrelated to recall: `state.db` is agent runtime state (cron, snapshots, etc.) and `kanban.db` is the multi-agent work queue. **Never describe them as "memory" to the user.**

## Curated memory — the only thing auto-injected

Source of record: `tools/memory_tool.py` → `MemoryStore`.

- **Files:** `$HERMES_HOME/memories/MEMORY.md` (agent notes) and `USER.md` (user profile). Plain UTF-8, entries separated by `\n§\n`.
- **Char limits (not tokens):** MEMORY.md = **2200 chars**, USER.md = **1375 chars**. `add` is rejected if it would exceed; agent must `replace`/`remove` first.
- **Injection model: frozen snapshot.** `load_from_disk()` runs **once at session start**, captures the rendered block into `_system_prompt_snapshot`, and `format_for_system_prompt()` returns that frozen copy for the whole session. Mid-session `memory(action=add|replace|remove)` writes to disk immediately but does **NOT** mutate the in-session system prompt. New entries become visible on the next session.
- **Why frozen:** keeping the system prompt byte-identical across turns preserves the provider's **prefix cache**. Mutating it per-turn would cache-bust every call and inflate token cost.
- **No filtering / no RAG.** The whole MEMORY.md and USER.md are concatenated and injected verbatim. There is no semantic ranking, no relevance pruning, no per-turn selection. The char-limit cap is the only mechanism keeping it bounded.
- **Header format (visible in the system prompt):**
  ```
  ══════════════════════════════════════════════
  MEMORY (your personal notes) [NN% — X,XXX/2,200 chars]
  ══════════════════════════════════════════════
  <entries joined by \n§\n>
  ```
  Same shape for USER under header `USER PROFILE (who the user is) [...]`.
- **Security scan on writes:** content is scanned for prompt-injection / exfil patterns + invisible Unicode before `add`/`replace` accepts it. Memory is in the system prompt so untrusted strings could hijack later turns.

## External provider memory (e.g. holographic / fact_store)

- Lives in a separate SQLite (commonly `$HERMES_HOME/memory_store.db`) managed by the provider plugin under `plugins/memory/<name>/`.
- Orchestrated by `agent/memory_manager.py` → `MemoryManager`. Lifecycle: `initialize → system_prompt_block (static) → prefetch (per-turn, often background-queued) → sync_turn → shutdown`.
- **Only one external provider** allowed at a time (enforced in `MemoryManager.add_provider` to avoid tool-schema bloat and conflicting backends). Builtin curated provider is always registered alongside.
- Prefetch output is wrapped in a `<memory-context>` fence with a system note tagging it as recalled context, not user input. `StreamingContextScrubber` strips this fence if it ever leaks into model output across streaming chunk boundaries.
- **Not part of the auto-injected curated memory.** When asked "is this auto-injected?", the answer is *only the provider's static `system_prompt_block()` is*; per-turn recall is on-demand via `prefetch()` and tool calls.

## Verification recipe (run before answering the user)

```bash
# Confirm where curated memory actually lives
ls -lah ~/.hermes/memories/
wc -c ~/.hermes/memories/MEMORY.md ~/.hermes/memories/USER.md

# Identify the OTHER .db files so you don't mis-attribute them
ls -lh ~/.hermes/*.db
# Expected typical set:
#   memory_store.db  → external memory provider (e.g. holographic), NOT curated memory
#   state.db         → agent runtime state (cron, snapshots, sessions index)
#   kanban.db        → multi-agent kanban board
```

If the user is on a profile, swap `~/.hermes/` for the active `HERMES_HOME` (find with `hermes config path` or read `$HERMES_HOME`).

## Pitfalls to avoid

1. **Do not claim "memory is in `memory_store.db`"** unless you've confirmed the user runs the holographic/external provider — and even then, curated memory is still the `.md` files. Misattributing the storage was the original mistake this reference exists to prevent.
2. **Do not describe curated memory as filtered/RAG/retrieval-based.** It's a flat full-text dump capped by char count. Saying otherwise oversells the system.
3. **Do not tell the user a `memory(add)` mid-session will affect the current turn's reasoning.** It only lands in the next session. If they need an instant change, they need `/reset` (or `/new`) after the write.
4. **Do not advise editing `MEMORY.md` or `USER.md` by hand during an active session.** Hermes uses `.lock` files and atomic temp-file rename via `_file_lock` + `atomic_replace`; manual edits with the session open can race with `save_to_disk()`. Safer: write via the `memory` tool, or edit only when no Hermes session is active.
5. **`memory_store.db` can be hundreds of MB.** That size is from the external provider's accumulated facts, not from anything injected into context. Don't conflate "big file" with "big context cost".

## When to update this file

Any time you discover new internals about how curated/external/session memory is loaded, scoped, or invalidated — especially around profile switching, `on_session_switch`, or `on_pre_compress`. Source files to re-read: `tools/memory_tool.py`, `agent/memory_manager.py`, `agent/memory_provider.py`, and whichever `plugins/memory/<name>/` is active.
