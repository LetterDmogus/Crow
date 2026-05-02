# Crow Skill 🐦‍⬛

> FTP harness for AI assistants with built-in Watch-out (Security & Monitoring) and smart project mapping.

## Overview
Crow allows AI assistants to interact with FTP servers safely and efficiently. It includes automatic backups, conflict detection, syntax validation, and bandwidth protection.

## AI-Preferred Commands
- `crow list [PATH]` : List files (Always do this before reading/writing).
- `crow read REMOTE` : Read file (Watch-out will block if >100KB).
- `crow write REMOTE CONTENT` : Write content (Use `-` for STDIN piping).
- `crow edit REMOTE` : Download -> Edit (local) -> Upload. Preferred for complex changes.
- `crow map` : Sync/Generate `FTP_TREE.md` project structure. Use `--refresh` for deep scans.
- `crow logs --watch` : Monitor remote error logs in real-time.
- `crow pull REMOTE [LOCAL]` : Download directory recursively (Safely ignores large/system folders).
- `crow push LOCAL [REMOTE]` : Upload directory recursively (Selective Sync: skips unchanged files).
- `crow search PATTERN` : Search for filenames in `FTP_TREE.md`. Use `--content` for remote text search.
- `crow diff REMOTE LOCAL` : Compare local changes with the server version before uploading.
- `crow tail REMOTE -n 50` : Quickly peek at logs or large files without consuming tokens.
- `crow delete REMOTE` : Delete a file (Automatically backed up to `.crow_backups/`).

## Watch-out System (Active by Default)

### 1. Conflict Detection (Versioning)
Crow tracks file versions in `.watchout/versions.json`. 
- **Behavior**: If a file is modified on the server by someone else after you read it, Crow will BLOCK your upload.
- **Action**: If blocked, you MUST `crow read` the file again to sync your context before retrying.

### 2. Large File Protection
- **Behavior**: Reading files > 100KB is blocked to save tokens and bandwidth.
- **Action**: Use `crow tail REMOTE -n 50` or `crow read REMOTE --force`.

### 3. Safety Guards (Linting & Secrets)
- **Syntax**: Crow runs `php -l`, `python ast`, and `json.loads` before uploading. Invalid syntax is BLOCKED.
- **Secrets**: Crow scans for API keys, passwords, and tokens. Leaks are BLOCKED.
- **Root Protection**: Destructive actions on `/` or systemic files (`.env`, `wp-config.php`) require `--force`.

### 4. Selective Sync (Efficiency)
- **Behavior**: `push` and `put` will SKIP files that haven't changed locally compared to the recorded remote version.
- **Action**: Trust the `Skipped` message; it means the server is already up to date.

### 5. Integrity Verify
- **Behavior**: After upload, Crow verifies remote file size. Mismatches trigger a FAILURE alert.

## Workflow Strategy
1. **Initialize**: `crow map` to understand the codebase.
2. **Research**: `crow search PATTERN` or `crow read` small files.
3. **Debug**: `crow logs --watch` while testing your changes.
4. **Deploy**: Use `crow edit` for single files or `crow push` for directory updates.
5. **Recover**: Local backups are kept in `.crow_backups/`.

## Important Constraints
- **Config**: Always check `.watchout/config.json` if you need to toggle features.
- **Force**: Only use `--force` if you are 100% certain of the change.
- **Ignore List**: Folders like `node_modules`, `vendor`, `.git`, and `.watchout` are ignored by default.
