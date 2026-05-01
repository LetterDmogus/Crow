# Crow Skill 🐦‍⬛

> FTP harness for AI assistants with built-in safeguards and smart project mapping.

## Overview
Crow allows you to interact with an FTP server via simple CLI commands. It includes automatic local backups, syntax validation, and AI-friendly editing modes.

## AI-Preferred Commands
- `crow skill` : Read this instruction file anytime.
- `crow search PATTERN` : **NEW** Fast filename search (uses local map). Use this first to find files!
- `crow search PATTERN --content --path PATH` : **NEW** Search for text inside files. **ALWAYS** specify a `--path` to keep it fast.
- `crow logs --tail` : Automatically find and tail the most relevant log file.
- `crow edit REMOTE --path-only` : Download a file to a local temp path for you to edit using your local tools.
- `crow diff REMOTE LOCAL` : Compare a remote file with your local version before overwriting.
- `cat local_file | crow write REMOTE -` : Safest way to write content. Prevents shell escaping issues.

## Core Commands
- `crow list [PATH]` : List files (respects `crow cd` context).
- `crow cd PATH` : Change virtual directory context.
- `crow read REMOTE` : Read file content (Smart lookup: `read index` works for `index.php`).
- `crow tail REMOTE -n 20` : Read last N lines. Use for logs!
- `crow map` : Sync/Generate `FTP_TREE.md` project structure.

## Safeguards (Active by Default)
1. **Local Backups**: Automatic download to `.crow_backups/` before any destructive action.
2. **PHP Linting**: Crow runs `php -l` locally before uploading. Upload is blocked if syntax is invalid.
3. **Smart Lookup**: If a file extension is missing, Crow tries to resolve it (e.g., `User` -> `User.php`).
4. **Protected Files**: `.htaccess`, `.env`, and `.ftp-tool.json` require `--force`.

## Working with Crow
1. **Explore**: Start by running `crow map` to understand the full structure.
2. **Locate**: Use `crow search "Keyword"` to find specific files without browsing folders.
3. **Diagnose**: Use `crow logs --tail` to see errors.
4. **Edit**: Use `crow edit <file> --path-only`, edit locally, then `crow put`.
5. **Safety**: Always check `crow diff` if you are unsure about overwriting a file.
6. **Writing**: Always use STDIN (`-`) for `crow write` if content contains `$`, `` ` ``, or `!`.
