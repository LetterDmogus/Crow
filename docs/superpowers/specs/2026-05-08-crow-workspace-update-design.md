# Crow Workspace Update Design Spec

**Date:** 2026-05-08
**Status:** Draft
**Topic:** Implementing `crow workspace update` to sync core files and bump manifest version.

## 1. Overview
As Crow evolves, core files like `CROW.md` and OS shortcuts may need updates to support new features (e.g., the Dashboard). `crow workspace update` provides a safe way to refresh these files while preserving the user's previous configuration via backups.

## 2. Goals
- Update `CROW.md` to the latest template.
- Refresh OS shortcuts (`.bat`, `.sh`) to ensure they point to the correct commands.
- Bump the manifest version from `2.0.0` to `2.0.1`.
- Ensure data safety by backing up existing core files.

## 3. Workflow
When a user runs `crow workspace update`:

### 3.1. Core File Refresh
1.  **CROW.md**:
    - Check if `CROW.md` exists.
    - If yes, rename it to `CROW.md.bak`.
    - Generate a fresh `CROW.md` with the latest options and placeholders.
2.  **OS Shortcuts**:
    - Re-run `generate_shortcut()` from `crow/workspace.py`.
    - This will overwrite existing `Crow Dashboard.bat` or `crow-dashboard.sh` with the latest logic.

### 3.2. Manifest Version Bump
1.  Load `.crow-manifest.json`.
2.  Update the `"version"` field from `"2.0.0"` to `"2.0.1"`.
3.  Save the manifest.

## 4. User Interaction
- The command will output a summary of changes:
    - `[info] Backed up CROW.md to CROW.md.bak`
    - `[success] Generated latest CROW.md`
    - `[success] Refreshed OS shortcuts`
    - `[success] Bumped manifest version to 2.0.1`

## 5. Technical Implementation
- **Command**: `crow workspace update`
- **Location**: Add to `crow/cli.py` and `crow/commands.py`.
- **Logic**: Use `os.rename` for backups and existing `generate_shortcut` / `Manifest` class methods.

## 6. Self-Review
- [x] **Placeholder scan**: No TBDs.
- [x] **Consistency**: Matches user preference (Option C: Overwrite with Backup).
- [x] **Scope**: focused on core file maintenance and versioning.
