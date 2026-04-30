# Crow Skill 🐦‍⬛

> FTP harness for AI assistants with built-in safeguards and project mapping.

## Overview
Crow allows you to interact with an FTP server via simple CLI commands. It includes automatic local backups and code validation to prevent accidental data loss or syntax errors.

## Core Commands
- `crow list [PATH]` : List files and directories.
- `crow read REMOTE` : Read file content (Warning: slow for large files).
- `crow tail REMOTE -n 20` : Read the last N lines of a file. **Use this for logs!**
- `crow write REMOTE CONTENT` : Overwrite or create a file (with backup & validation).
- `crow edit REMOTE` : Human-like workflow (Download -> Local Edit -> Upload).
- `crow map` : Generate `FTP_TREE.md` to understand project structure (Laravel-friendly).
- `crow info` : Show active connection details.

## Safeguards (Active by Default)
1. **Local Backups**: Before any `write`, `delete`, or `edit`, the existing file is downloaded to `.crow_backups/` locally.
2. **Protected Files**: Files like `.htaccess`, `.env`, and `wp-config.php` cannot be modified without the `--force` flag.
3. **Syntax Validation**:
   - **Python**: Checked for `SyntaxError`.
   - **PHP**: Checked for missing `<?php` tags.
   - **General**: Prevents writing empty/whitespace-only content.
4. **Project Mapping**: `crow map` helps you locate Controllers, Models, and Views without scanning every folder manually. It ignores heavy folders like `vendor/` and `node_modules/`.

## Integration Instructions
When working on this project, always check `FTP_TREE.md` first to understand the structure. 
**If you need to check logs, ALWAYS use `crow tail` to save bandwidth and context.** 
If you need to modify a file, use `crow read` (only for small/medium files), then `crow write` to apply changes.

Example:
"Use `crow tail error_log` to see the latest errors before attempting to fix them."
