# Environment-Specific Adaptations for Hermes Backup

Real-world pitfalls encountered when deploying the backup solution across different environments.

## 1. sqlite3 CLI Not Available

**Problem**: Many minimal Linux distributions or containers do not ship the `sqlite3` command-line tool.

**Symptom**:
```
which sqlite3  # → "sqlite3 not in PATH"
```

**Solution**: Use Python's built-in `sqlite3` module for ALL database operations. Never depend on the `sqlite3` CLI in scripts.

```python
# Good — works everywhere Python is installed
python3 -c "import sqlite3; conn = sqlite3.connect('...'); ..."

# Bad — fails on minimal systems
sqlite3 memory_store.db < dump.sql
```

**Impact**: Both `export.sh` and `import.sh` must use Python exclusively for DB operations.

---

## 2. numpy Only in Hermes venv

**Problem**: The `rebuild_all_vectors()` call requires `numpy`, but it's often only installed inside the Hermes Agent's virtual environment (`~/.hermes/hermes-agent/venv/`), not in the system Python.

**Symptom**:
```
/usr/bin/python3: No module named numpy
```

**Solution**: The rebuild script must:
1. First try importing numpy in the current interpreter
2. If missing, check if `~/.hermes/hermes-agent/venv/bin/python` exists and has numpy
3. If yes, `os.execv()` to restart itself under that interpreter
4. As last resort, try installing numpy

```python
HERMES_VENV_PYTHON = os.path.join(HERMES_HOME, "hermes-agent", "venv", "bin", "python")

def _ensure_numpy() -> bool:
    try:
        import numpy
        return True
    except ImportError:
        pass

    if os.path.exists(HERMES_VENV_PYTHON):
        result = subprocess.run(
            [HERMES_VENV_PYTHON, "-c", "import numpy; print('ok')"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and "ok" in result.stdout:
            os.execv(HERMES_VENV_PYTHON, [HERMES_VENV_PYTHON] + sys.argv)
    # ... fallback to install
```

**Impact**: `rebuild_vectors.py` must be a standalone script with venv detection, not an inline Python snippet in `import.sh`.

---

## 3. Hermes Data Directory (`~/hermes_data`)

**Problem**: Users often maintain a separate working data directory (e.g., `~/hermes_data`) for analysis outputs, collected data, and reports. This directory is distinct from `~/.hermes` (the Hermes Agent runtime directory) but equally valuable.

**Solution**: Include `~/hermes_data` in the backup scope, with these exclusions:
- `venv/`, `.venv/`, `env/` — Python virtual environments (rebuildable)
- `logs/`, `*.log` — Temporary logs
- `*.db`, `*.db-wal`, `*.db-shm` — SQLite binaries
- `__pycache__/`, `*.pyc` — Python cache
- `cache/`, `node_modules/` — Application caches

```bash
rsync -a --delete \
    --exclude='venv' --exclude='.venv' --exclude='env' \
    --exclude='__pycache__' --exclude='*.pyc' \
    --exclude='logs' --exclude='*.log' \
    --exclude='*.db' --exclude='*.db-wal' --exclude='*.db-shm' \
    --exclude='.DS_Store' --exclude='*.tmp' --exclude='*.temp' \
    --exclude='*.bak' --exclude='*.backup' \
    --exclude='cache' --exclude='node_modules' \
    "$SRC_DATA/" "$DST/hermes_data/"
```

---

## 4. Python Package Name Restrictions

**Problem**: The Hermes holographic memory plugin lives at `~/.hermes/hermes-agent/plugins/memory/holographic/`. You cannot `sys.path.insert()` and then `import holographic.store` because Python package names with hyphens (`hermes-agent`) are not valid.

**Solution**: Copy `store.py` and `holographic.py` to a temporary directory with a clean package name, then use `importlib.util.load_module_from_path()`.

```python
with tempfile.TemporaryDirectory() as tmpdir:
    pkg_dir = os.path.join(tmpdir, "holo_rebuild")
    os.makedirs(pkg_dir, exist_ok=True)
    shutil.copy2(os.path.join(SRC_DIR, "holographic.py"), pkg_dir)
    shutil.copy2(os.path.join(SRC_DIR, "store.py"), pkg_dir)

    hrr_mod = load_module_from_path("holographic_rebuild_hrr", os.path.join(pkg_dir, "holographic.py"))
    sys.modules["holographic"] = hrr_mod
    store_mod = load_module_from_path("holographic_rebuild_store", os.path.join(pkg_dir, "store.py"))
```

---

## 5. config.yaml 脱敏遗漏

**Problem**: The original regex only matched `api_key`. Some configs also use `api_secret` or `token`.

**Expanded regex**:
```python
redacted = re.sub(r'^(\s*api_key:\s*)(\S+)$', r'\1__REPLACE_WITH_YOUR_KEY__', raw, flags=re.MULTILINE)
redacted = re.sub(r'^(-\s*api_key:\s*)(\S+)$', r'\1__REPLACE_WITH_YOUR_KEY__', redacted, flags=re.MULTILINE)
redacted = re.sub(r'^(\s*api_secret:\s*)(\S+)$', r'\1__REPLACE_WITH_YOUR_SECRET__', redacted, flags=re.MULTILINE)
redacted = re.sub(r'^(\s*token:\s*)(\S+)$', r'\1__REPLACE_WITH_YOUR_TOKEN__', redacted, flags=re.MULTILINE)
```
