import sys
import argparse
from crow import commands

def build_parser():
    # 1. Create a parent parser for shared arguments
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("--config", help="Path to config file")
    parent_parser.add_argument("--force", action="store_true", help="Bypass validation")
    parent_parser.add_argument("--id", help="Session ID (default: default)")

    parser = argparse.ArgumentParser(
        prog="crow",
        description="FTP harness for AI assistants",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
commands:
  init              Create .ftp-tool.json config
  info              Show active config
  cd PATH           Change virtual CWD for a session
  shell             Start interactive shell
  dashboard         Start health dashboard
  list [PATH]       List remote directory
  put LOCAL [REMOTE] Upload file
  read REMOTE       Print file content
  tail REMOTE       Read last N lines
  write REMOTE CONTENT Write to file (use - for STDIN)
  diff REMOTE LOCAL Compare remote and local file
  logs              Discover and tail log files
  delete REMOTE     Delete file
  mkdir REMOTE      Create directory
  edit REMOTE       Download → Edit → Upload
  scan [PATHS...]   Scan and sync files/folders
  migrate           Upgrade from v1 to v2
  workspace init    Initialize virtual workspace
  workspace status  Show workspace status
  workspace sync    Force sync manifest with server
  workspace update  Refresh core files and bump manifest version
  watch start       Start watching for local changes
"""
    )

    sub = parser.add_subparsers(dest="command")

    # watch group
    p_watch = sub.add_parser("watch", parents=[parent_parser], help="Watching agent management")
    watch_sub = p_watch.add_subparsers(dest="subcommand")
    
    # watch start
    watch_sub.add_parser("start", help="Start watcher")

    # workspace group
    p_ws = sub.add_parser("workspace", parents=[parent_parser], help="Virtual workspace management")
    ws_sub = p_ws.add_subparsers(dest="subcommand")

    # workspace init
    p_ws_init = ws_sub.add_parser("init", help="Initialize workspace")
    p_ws_init.add_argument("--preset", choices=["laravel"], help="Preset for auto-ignore")

    # workspace status
    p_ws_status = ws_sub.add_parser("status", help="Show workspace status")
    p_ws_status.add_argument("--list", action="store_true", help="List files for each status")

    # workspace sync
    p_ws_sync = ws_sub.add_parser("sync", help="Force sync manifest")

    # workspace update
    ws_sub.add_parser("update", help="Refresh core files and bump manifest version")

    # init
    sub.add_parser("init", parents=[parent_parser], help="Create config")
    # info
    sub.add_parser("info", parents=[parent_parser], help="Show active config")
    # shell
    sub.add_parser("shell", parents=[parent_parser], help="Start interactive shell")
    # dashboard
    sub.add_parser("dashboard", parents=[parent_parser], help="Start health dashboard")
    # browse (deprecated)
    sub.add_parser("browse", parents=[parent_parser])

    # cd
    p_cd = sub.add_parser("cd", parents=[parent_parser], help="Change virtual CWD")
    p_cd.add_argument("path", help="Remote directory path")

    # list
    p_list = sub.add_parser("list", parents=[parent_parser], help="List remote directory")
    p_list.add_argument("path", nargs="?", default=None, help="Remote path")

    # put
    p_put = sub.add_parser("put", parents=[parent_parser], help="Upload file")
    p_put.add_argument("local", help="Local file path")
    p_put.add_argument("remote", nargs="?", default=None, help="Remote destination")

    # read
    p_read = sub.add_parser("read", parents=[parent_parser], help="Print file content")
    p_read.add_argument("remote", help="Remote file path")

    # tail
    p_tail = sub.add_parser("tail", parents=[parent_parser], help="Read last N lines")
    p_tail.add_argument("remote", help="Remote file path")
    p_tail.add_argument("-n", "--lines", default=20, help="Number of lines")

    # logs
    p_logs = sub.add_parser("logs", parents=[parent_parser], help="Discover log files")
    p_logs.add_argument("--tail", action="store_true", help="Automatically tail the first log found")
    p_logs.add_argument("--watch", action="store_true", help="Monitor the log for new errors in real-time")

    # diff
    p_diff = sub.add_parser("diff", parents=[parent_parser], help="Compare remote and local")
    p_diff.add_argument("remote", help="Remote file path")
    p_diff.add_argument("local", help="Local file path")

    # search
    p_search = sub.add_parser("search", parents=[parent_parser], help="Search for filenames or content")
    p_search.add_argument("pattern", help="Regex or string to search for")
    p_search.add_argument("--content", action="store_true", help="Search inside file content (heavy)")
    p_search.add_argument("--path", help="Limit content search to this path")

    # write
    p_write = sub.add_parser("write", parents=[parent_parser], help="Write content")
    p_write.add_argument("remote", help="Remote file path")
    p_write.add_argument("content", help="Content to write")

    # delete
    p_del = sub.add_parser("delete", parents=[parent_parser], help="Delete file")
    p_del.add_argument("remote", help="Remote file path")

    # mkdir
    p_mkdir = sub.add_parser("mkdir", parents=[parent_parser], help="Create directory")
    p_mkdir.add_argument("remote", help="Remote directory path")

    # edit
    p_edit = sub.add_parser("edit", parents=[parent_parser], help="Edit file")
    p_edit.add_argument("remote", help="Remote file path")
    p_edit.add_argument("--path-only", action="store_true", help="Download and return path for AI editing")

    # scan
    p_scan = sub.add_parser("scan", parents=[parent_parser], help="Scan and sync files/folders")
    p_scan.add_argument("paths", nargs="+", help="Paths to scan")
    p_scan.add_argument("--depth", type=int, choices=[1, 2, 3], default=1, help="Recursion depth (max 3)")
    p_scan.add_argument("--get", action="store_true", help="Download file content (hydrate)")

    # migrate
    sub.add_parser("migrate", parents=[parent_parser], help="Upgrade v1 to v2")

    return parser

def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    dispatch = {
        "init":   commands.cmd_init,
        "info":   commands.cmd_info,
        "cd":     commands.cmd_cd,
        "shell":  commands.cmd_shell,
        "dashboard": commands.cmd_dashboard,
        "browse": commands.cmd_browse,
        "list":   commands.cmd_list,
        "put":    commands.cmd_put,
        "read":   commands.cmd_read,
        "tail":   commands.cmd_tail,
        "logs":   commands.cmd_logs,
        "diff":   commands.cmd_diff,
        "search": commands.cmd_search,
        "write":  commands.cmd_write,
        "delete": commands.cmd_delete,
        "mkdir":  commands.cmd_mkdir,
        "edit":   commands.cmd_edit,
        "scan":   commands.cmd_scan,
        "migrate": commands.cmd_migrate,
        "workspace": commands.cmd_workspace,
        "watch":  commands.cmd_watch,
    }

    fn = dispatch.get(args.command)
    if fn:
        fn(args)
    else:
        print(f"[crow] ERROR: Unknown command: {args.command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
