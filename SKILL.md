# Crow Skill v2 🐦‍⬛

> FTP harness for AI assistants with Virtual Workspace and Auto-Sync.

## Overview
As an AI, you work inside the `workspace/` folder. Files here are initially 0kb (skeletons). You must "hydrate" them before reading or editing.

## Essential AI Commands
- `crow scan PATH --get` : **MANDATORY** before reading a 0kb file. Downloads content into the workspace.
- `crow scan PATH --depth 2` : Update folder structure without downloading content.
- `crow workspace status --list` : Check which files are already synced or still skeletons.
- `crow list [PATH]` : Standard FTP directory listing.
- `crow read REMOTE` : Read file content (Use only if file is not in workspace).
- `crow edit REMOTE` : Quick download -> edit -> upload for files outside workspace.

## AI Workflow
1. **Explore**: Use `crow workspace status --list` or `ls` in the `workspace/` folder to see what's available.
2. **Hydrate**: If a file you need to read/edit is 0kb, run `crow scan <path> --get`.
3. **Edit**: Modify files directly in the `workspace/` folder.
4. **Sync**: A background Watcher Agent is usually running. Your saves are auto-uploaded.

## Error Handling & Human Interaction
- **Blocked Upload**: If the Watcher or a manual push is blocked due to conflict, **ask the human** to resolve it (usually by running `crow scan <path> --get` to pull the latest version).
- **Permissions**: If you get a "Permission Denied" error, ask the human to check FTP user rights.
- **Large Scans**: If you need to scan deep (depth > 3), ask the human for permission as it might be slow.
- **Watcher Prompts**: If you create a NEW file, the Watcher will ask for confirmation (y/n) in its terminal. Inform the human that you've created a file and they need to confirm it in the Watcher terminal.
