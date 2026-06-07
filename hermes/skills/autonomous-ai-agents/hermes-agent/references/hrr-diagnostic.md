---
name: hermes-holographic-hrr-diagnostic
description: |
  Systematically diagnose whether Hermes Agent's holographic HRR memory is actually working.
  Checks configuration, numpy availability, database schema compatibility, and write operations.
  Identifies common "fake enabled" issues where HRR is configured but non-functional.
tags: [hermes, holographic, hrr, memory, diagnostic, debugging]
---

# Hermes Holographic HRR Memory Diagnostic

## When to Use

When the user suspects HRR (Holographic Reduced Representations) memory is not working, or wants to verify its actual operational status.

Common symptoms:
- `fact_store` search works but `probe`/`reason`/`contradict` return poor results
- Memory feels like plain keyword search instead of algebraic retrieval
- New facts fail to insert with `OperationalError`

## Diagnostic Steps

### Step 1: Check Configuration

Verify the active Hermes profile configuration includes:

```yaml
memory:
  provider: holographic          # MUST be "holographic"

plugins:
  hermes-memory-store:
    hrr_dim: '4096'              # Should be > 0 (default 1024)
    db_path: ~/.hermes/memory_store.db
```

Use `hermes config` or inspect the profile's config file directly.

### Step 2: Verify numpy Availability

Ensure numpy is installed in the Hermes virtual environment:

```bash
cd ~/.hermes/hermes-agent && source venv/bin/activate
python3 -c "import numpy; print(numpy.__version__)"
```

Also verify `_HAS_NUMPY` in the HRR module:
```python
from plugins.memory.holographic import holographic as hrr
print(hrr._HAS_NUMPY)
```

### Step 3: Inspect Database Schema

Connect to the memory SQLite database (default: `~/.hermes/memory_store.db`) and verify schema compatibility:

**Critical compatibility checkpoints:**

| Plugin Expects | Actual DB | Check Command |
|---|---|---|
| `facts` table with `fact_id` column | May have `id` instead | `PRAGMA table_info(facts)` |
| `fact_entities(fact_id, entity_id)` | May have `entity` text | `PRAGMA table_info(fact_entities)` |
| `facts_fts(content, tags)` | May have `content` only | `PRAGMA table_info(facts_fts)` |
| `entities` table with rows | May be empty | `SELECT COUNT(*) FROM entities` |

### Step 4: Check HRR Vector Coverage

Run this SQL against the memory database:

```sql
SELECT
  COUNT(*) as total_facts,
  COUNT(hrr_vector) as with_hrr,
  COUNT(*) - COUNT(hrr_vector) as without_hrr,
  ROUND(COUNT(hrr_vector) * 100.0 / COUNT(*), 1) as coverage_pct
FROM facts;
```

**Expected**: coverage_pct > 0%
**Problem**: coverage_pct = 0% means HRR vectors were never generated

### Step 5: Test Live Write Operation

Programmatically test inserting a fact via the MemoryStore class:

```python
from plugins.memory.holographic.store import MemoryStore

store = MemoryStore(
    db_path='~/.hermes/memory_store.db',
    default_trust=0.5,
    hrr_dim=4096
)

# Test insert
try:
    fid = store.add_fact("HRR diagnostic test fact", category="test")
    print(f"Insert OK: fact_id={fid}")
except Exception as e:
    print(f"Insert FAILED: {e}")
    # Common failure: "table facts_fts has no column named tags"
```

## Common Issues & Fixes

### Issue: "fake enabled" — config says holographic but DB has wrong schema

**Root cause**: The database was created by a different tool (e.g., an older import script or different memory plugin) before the holographic plugin was enabled. The holographic plugin expects a specific schema but finds an incompatible one.

**Fix — Rebuild database:**
1. Back up the existing database file with a timestamp suffix
2. Trigger the holographic plugin to initialize a fresh database by attempting a `fact_store` add operation
3. The plugin auto-creates tables on first use
4. Migrate old data from backup if needed by re-inserting via `fact_store`

### Issue: numpy not available

**Fix**: Ensure numpy is present in the Hermes virtual environment.

### Issue: 0% HRR coverage on existing facts

**Fix**: If schema is correct but old facts lack vectors, the plugin does not retroactively generate them. Options:
1. Re-insert facts via `fact_store` (triggers `_compute_hrr_vector`)
2. Write a batch migration script that calls `store._compute_hrr_vector(fact_id, content)` for each row

## Verification Checklist

- [ ] `memory.provider` is `holographic` in the active config
- [ ] `hrr_dim` is set and > 0
- [ ] `numpy` is installed and importable in the Hermes Python environment
- [ ] `facts` table has `fact_id` (not `id`) as primary key
- [ ] `fact_entities` has `entity_id` column (not `entity` text)
- [ ] `facts_fts` has both `content` and `tags` columns
- [ ] `entities` table is populated (not empty)
- [ ] HRR coverage > 0% (or new inserts generate vectors)
- [ ] Live `add_fact()` succeeds without `OperationalError`

## Pitfalls

- **Do NOT** manually create the SQLite DB schema. Always let the holographic plugin initialize it via `MemoryStore._init_db()`.
- **Schema mismatches are silent** — the plugin may load without error but fail on write, making it look like HRR is working when it's not.
- **FTS5 triggers** are the canary: if `add_fact()` fails with "no such column", the schema is definitely wrong.
