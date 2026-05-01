import cmd
import shlex
import os
from types import SimpleNamespace
from rich.table import Table
from rich.syntax import Syntax
from rich.panel import Panel
from crow import commands
from crow.core import get_cwd, load_sessions
from crow.utils import console

class CrowShell(cmd.Cmd):
    def __init__(self):
        super().__init__()
        self.current_id = "default"
        self.update_prompt()

    def update_prompt(self):
        cwd = get_cwd(self.current_id)
        # Magenta for ID, Cyan for CWD
        self.prompt = f"\033[1;35m[id:{self.current_id}]\033[0m \033[36m{cwd}\033[0m > "

    def preloop(self):
        console.print(Panel.fit(
            "[bold green]Crow Interactive Shell[/]\n"
            "Type [cyan]help[/] or [cyan]?[/] to list commands.",
            border_style="magenta"
        ))

    def do_exit(self, arg):
        """Exit the shell."""
        console.print("[bold yellow]Goodbye! 🐦‍⬛[/]")
        return True

    def do_use(self, arg):
        """Switch session ID: use <id>"""
        if not arg:
            console.print(f"Current session: [session]{self.current_id}[/]")
            return
        self.current_id = arg
        self.update_prompt()
        console.print(f"Switched to session: [session]{self.current_id}[/]")

    def do_status(self, arg):
        """Show all active sessions in a nice table."""
        sessions = load_sessions()
        table = Table(title="Crow Active Sessions", show_header=True, header_style="bold magenta")
        table.add_column("Status", justify="center", style="dim")
        table.add_column("Session ID", style="cyan")
        table.add_column("Current Working Directory", style="green")

        for sid, cwd in sessions.items():
            marker = "▶" if sid == self.current_id else ""
            table.add_row(marker, sid, cwd)
        
        console.print(table)

    def do_ls(self, arg):
        """List directory: ls [path]"""
        args = SimpleNamespace(id=self.current_id, path=arg or None)
        commands.cmd_list(args)
        self.update_prompt()

    def do_cd(self, arg):
        """Change directory: cd <path>"""
        if not arg: return
        args = SimpleNamespace(id=self.current_id, path=arg)
        commands.cmd_cd(args)
        self.update_prompt()

    def do_read(self, arg):
        """Read file with syntax highlighting: read <path>"""
        if not arg: return
        args = SimpleNamespace(id=self.current_id, remote=arg)
        content = commands.get_remote_content(args)
        if content:
            ext = os.path.splitext(arg)[1] or ".txt"
            syntax = Syntax(content, ext.strip("."), theme="monokai", line_numbers=True)
            console.print(syntax)

    def do_cat(self, arg):
        """Alias for read"""
        self.do_read(arg)

    def do_tail(self, arg):
        """Tail file: tail <path> [lines]"""
        parts = shlex.split(arg)
        if not parts: return
        remote = parts[0]
        lines = parts[1] if len(parts) > 1 else 20
        args = SimpleNamespace(id=self.current_id, remote=remote, lines=lines)
        commands.cmd_tail(args)

    def do_write(self, arg):
        """Write file: write <path> <content>"""
        parts = shlex.split(arg)
        if len(parts) < 2:
            console.print("[warning]Usage:[/] write <path> <content>")
            return
        args = SimpleNamespace(id=self.current_id, remote=parts[0], content=parts[1], force=False)
        commands.cmd_write(args)

    def do_edit(self, arg):
        """Edit remote file: edit <path>"""
        if not arg: return
        args = SimpleNamespace(id=self.current_id, remote=arg, force=False)
        commands.cmd_edit(args)

    def do_rm(self, arg):
        """Delete file: rm <path>"""
        if not arg: return
        args = SimpleNamespace(id=self.current_id, remote=arg, force=False)
        commands.cmd_delete(args)

    def do_mkdir(self, arg):
        """Make directory: mkdir <path>"""
        if not arg: return
        args = SimpleNamespace(id=self.current_id, remote=arg)
        commands.cmd_mkdir(args)

    def do_map(self, arg):
        """Generate/Sync FTP_TREE.md"""
        args = SimpleNamespace(id=self.current_id, refresh=('--refresh' in arg))
        commands.cmd_map(args)

    def do_clear(self, arg):
        """Clear screen"""
        os.system('clear' if os.name == 'posix' else 'cls')

    # Aliases & basic overrides
    def emptyline(self): pass
    do_list = do_ls
    do_delete = do_rm
    do_quit = do_exit
