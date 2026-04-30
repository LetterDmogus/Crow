import sys
import argparse
from crow import commands

def build_parser():
    parser = argparse.ArgumentParser(
        prog="crow",
        description="FTP harness for AI assistants",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
commands:
  init              Create .ftp-tool.json config interactively
  info              Show active config (password masked)
  list [PATH]       List remote directory
  get REMOTE [LOCAL] Download file from server
  put LOCAL [REMOTE] Upload file to server
  read REMOTE       Print remote file contents to stdout
  write REMOTE CONTENT Write content string to remote file (use - for stdin)
  delete REMOTE     Delete remote file
  mkdir REMOTE      Create remote directory
  edit REMOTE       Download → open in $EDITOR → re-upload
  map               Generate FTP_TREE.md structure locally
  pull REMOTE [LOCAL] Download a remote directory recursively
  push LOCAL [REMOTE] Upload a local directory recursively
"""
    )
    parser.add_argument("--config", help="Path to config file (default: auto-detect)")
    parser.add_argument("--force", action="store_true", help="Bypass validation and safety checks")

    sub = parser.add_subparsers(dest="command")

    # init
    sub.add_parser("init", help="Create config interactively")
    sub.add_parser("info", help="Show active config")

    # list
    p_list = sub.add_parser("list", help="List remote directory")
    p_list.add_argument("path", nargs="?", default=None, help="Remote path")

    # get
    p_get = sub.add_parser("get", help="Download remote file")
    p_get.add_argument("remote", help="Remote file path")
    p_get.add_argument("local", nargs="?", default=None, help="Local destination")

    # put
    p_put = sub.add_parser("put", help="Upload local file")
    p_put.add_argument("local", help="Local file path")
    p_put.add_argument("remote", nargs="?", default=None, help="Remote destination")

    # read
    p_read = sub.add_parser("read", help="Print remote file to stdout")
    p_read.add_argument("remote", help="Remote file path")

    # write
    p_write = sub.add_parser("write", help="Write content to remote file")
    p_write.add_argument("remote", help="Remote file path")
    p_write.add_argument("content", help="Content to write")

    # delete
    p_del = sub.add_parser("delete", help="Delete remote file")
    p_del.add_argument("remote", help="Remote file path")

    # mkdir
    p_mkdir = sub.add_parser("mkdir", help="Create remote directory")
    p_mkdir.add_argument("remote", help="Remote directory path")

    # edit
    p_edit = sub.add_parser("edit", help="Edit remote file locally")
    p_edit.add_argument("remote", help="Remote file path")

    # map
    p_map = sub.add_parser("map", help="Generate FTP_TREE.md structure")
    p_map.add_argument("--refresh", action="store_true", help="Force scan")

    # pull
    p_pull = sub.add_parser("pull", help="Download a remote directory recursively")
    p_pull.add_argument("remote", help="Remote directory path")
    p_pull.add_argument("local", nargs="?", default=None, help="Local destination path")

    # push
    p_push = sub.add_parser("push", help="Upload a local directory recursively")
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
        "list":   commands.cmd_list,
        "get":    commands.cmd_get,
        "put":    commands.cmd_put,
        "read":   commands.cmd_read,
        "tail":   commands.cmd_tail,
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
s.cmd_push,
    }

    fn = dispatch.get(args.command)
    if fn:
        fn(args)
    else:
        print(f"[crow] ERROR: Unknown command: {args.command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
