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
  skill             Print SKILL.md for AI context
  cd PATH           Change virtual CWD for a session
  shell             Start interactive shell
  browse            Start TUI browser
  list [PATH]       List remote directory
  get REMOTE [LOCAL] Download file
  put LOCAL [REMOTE] Upload file
  read REMOTE       Print file content
  tail REMOTE       Read last N lines
  write REMOTE CONTENT Write to file (use - for STDIN)
  diff REMOTE LOCAL Compare remote and local file
  logs              Discover and tail log files
  delete REMOTE     Delete file
  mkdir REMOTE      Create directory
  edit REMOTE       Download → Edit → Upload
  map               Generate FTP_TREE.md
  pull REMOTE [LOCAL] Download directory recursively
  push LOCAL [REMOTE] Upload directory recursively
"""
    )

    sub = parser.add_subparsers(dest="command")

    # init
    sub.add_parser("init", parents=[parent_parser], help="Create config")
    # info
    sub.add_parser("info", parents=[parent_parser], help="Show active config")
    # skill
    sub.add_parser("skill", parents=[parent_parser], help="Print SKILL.md")
    # shell
    sub.add_parser("shell", parents=[parent_parser], help="Start interactive shell")
    # browse
    sub.add_parser("browse", parents=[parent_parser], help="Start TUI browser")

    # cd
    p_cd = sub.add_parser("cd", parents=[parent_parser], help="Change virtual CWD")
    p_cd.add_argument("path", help="Remote directory path")

    # list
    p_list = sub.add_parser("list", parents=[parent_parser], help="List remote directory")
    p_list.add_argument("path", nargs="?", default=None, help="Remote path")

    # get
    p_get = sub.add_parser("get", parents=[parent_parser], help="Download file")
    p_get.add_argument("remote", help="Remote file path")
    p_get.add_argument("local", nargs="?", default=None, help="Local destination")

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

    # map
    p_map = sub.add_parser("map", parents=[parent_parser], help="Generate FTP_TREE.md")
    p_map.add_argument("--refresh", action="store_true", help="Force scan")

    # pull
    p_pull = sub.add_parser("pull", parents=[parent_parser], help="Download directory recursively")
    p_pull.add_argument("remote", help="Remote directory path")
    p_pull.add_argument("local", nargs="?", default=None, help="Local destination path")

    # push
    p_push = sub.add_parser("push", parents=[parent_parser], help="Upload directory recursively")
    p_push.add_argument("local", help="Local directory path")
    p_push.add_argument("remote", nargs="?", default=None, help="Remote destination path")

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
        "skill":  commands.cmd_skill,
        "cd":     commands.cmd_cd,
        "shell":  commands.cmd_shell,
        "browse": commands.cmd_browse,
        "list":   commands.cmd_list,
        "get":    commands.cmd_get,
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
        "map":    commands.cmd_map,
        "pull":   commands.cmd_pull,
        "push":   commands.cmd_push,
    }

    fn = dispatch.get(args.command)
    if fn:
        fn(args)
    else:
        print(f"[crow] ERROR: Unknown command: {args.command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
