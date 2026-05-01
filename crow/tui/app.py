import os
import threading
import subprocess
import tempfile
import asyncio
from pathlib import Path
from types import SimpleNamespace

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, DataTable, Log, Input
from textual.containers import Container, Horizontal, Vertical
from textual import work, on
from rich.text import Text
from rich.syntax import Syntax

from crow.core import connect, load_config, get_cwd, load_sessions, save_sessions
from crow import commands
from crow.commands import parse_ftp_line

def get_icon(name: str, is_dir: bool) -> str:
    """Return a fixed-width icon for layout stability."""
    if is_dir: return "dir "
    ext = os.path.splitext(name)[1].lower()
    if name == ".env": return "env "
    if name == ".htaccess": return "cfg "
    icons = {
        ".php": "php ", ".py": "py  ", ".md": "md  ", ".json": "json",
        ".sql": "sql ", ".js": "js  ", ".css": "css ", ".html": "html",
        ".jpg": "img ", ".png": "img ", ".zip": "zip ",
    }
    return icons.get(ext, "file")

class Sidebar(Vertical):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.can_focus = True

class CrowBrowser(App):
    """Crow TUI V1.7.0 - Integrated Shell and Pro Navigation."""
    
    CSS = """
    Screen { background: transparent; }
    Sidebar { width: 20%; border-right: solid $primary; }
    Sidebar:focus { background: $boost; border-right: double $accent; }
    #content { width: 55%; }
    #right-panel { width: 25%; border-left: solid $primary; }
    #preview-area { height: 65%; border-bottom: solid $primary; }
    #log-area { height: 35%; }
    .title {
        text-align: center; width: 100%; color: $accent; text-style: bold;
        border-bottom: solid $primary; margin-bottom: 0; padding: 0 1;
    }
    #search-bar { display: none; margin: 0 1; border: tall $accent; }
    #search-bar.-visible { display: block; }
    DataTable { background: transparent; border: none; height: 1fr; }
    DataTable:focus { border-left: double $accent; }
    Log { background: transparent; color: $text-muted; }
    #preview-box { padding: 0; margin: 0; height: 100%; overflow: hidden; }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("h", "go_home", "Home"),
        ("/", "toggle_search", "Search"),
        ("e", "edit_file", "Edit"),
        ("s", "toggle_panel", "Switch Panel"),
        (":", "open_shell", "Shell"), # NEW: Open Shell
        ("space", "show_preview", "Preview"),
        ("backspace", "parent_dir", "Back"),
        ("left", "parent_dir", "Back"),
        ("right", "enter_item", "Forward"),
    ]

    def __init__(self):
        super().__init__()
        self.current_id = "default"
        self.selected_id = "default"
        self.current_path = get_cwd(self.current_id)
        self.all_items = []
        self._main_thread = threading.get_ident()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main-container"):
            with Horizontal():
                with Sidebar(id="sidebar"):
                    yield Static("SESSIONS", classes="title")
                    yield Static("", id="session-info")
                with Vertical(id="content"):
                    yield Static("REMOTE FILES", classes="title")
                    yield Input(placeholder="Search files...", id="search-bar")
                    table = DataTable(id="file-table")
                    table.add_columns("Name", "Size", "Modified")
                    table.cursor_type = "row"
                    yield table
                with Vertical(id="right-panel"):
                    with Vertical(id="preview-area"):
                        yield Static("PREVIEW", classes="title")
                        yield Static("Select a file and press Space...", id="preview-box")
                    with Vertical(id="log-area"):
                        yield Static("ACTIVITY LOG", classes="title")
                        yield Log(id="cmd-log")
        yield Footer()

    def on_mount(self) -> None:
        self.update_session_info()
        self.log_message("Crow TUI V1.7 started.")
        self.query_one(DataTable).focus()
        self.action_refresh()

    def log_message(self, msg: str):
        try: self.query_one("#cmd-log", Log).write_line(f"> {msg}")
        except: pass

    def update_session_info(self):
        sessions = load_sessions()
        info_text = "\n"
        for sid in sessions:
            marker = ""
            if sid == self.current_id: marker += "▶"
            if sid == self.selected_id: marker += " ❯"
            style = "bold cyan" if sid == self.selected_id else "white"
            info_text += f"  {marker:3} [{style}]{sid}[/]\n"
        self.query_one("#session-info", Static).update(info_text)

    def safe_update(self, func, *args, **kwargs):
        if threading.get_ident() == self._main_thread: func(*args, **kwargs)
        else: self.call_from_thread(func, *args, **kwargs)

    @work(exclusive=True, thread=True)
    def action_refresh(self):
        self.log_message(f"Entering: {self.current_path}")
        table = self.query_one(DataTable)
        self.safe_update(table.clear)
        self.all_items = []
        try:
            cfg = load_config(); ftp = connect(cfg)
            entries = []; ftp.retrlines(f"LIST {self.current_path}", entries.append); ftp.quit()
            for line in entries:
                item = parse_ftp_line(line)
                if not item or not item["name"] or item["name"].strip() in (".", ".."): continue
                self.all_items.append(item)
                icon = get_icon(item["name"], item["is_dir"])
                display_name = Text(f"{icon} {item['name']}")
                if item["is_dir"]: display_name.stylize("bold green")
                self.safe_update(table.add_row, display_name, item["size"], item["modified"], key=f"{item['name']}|{item['is_dir']}")
            self.log_message(f"Loaded {len(self.all_items)} items.")
        except Exception as e: self.log_message(f"ERROR: {e}")

    def action_show_preview(self):
        table = self.query_one(DataTable)
        if table.cursor_row is not None:
            try:
                row_keys = list(table.rows.keys())
                if table.cursor_row < len(row_keys):
                    self.update_preview(row_keys[table.cursor_row].value)
            except: pass

    @work(exclusive=True, thread=True)
    def update_preview(self, row_key_value: str):
        if not row_key_value: return
        name, is_dir = row_key_value.split("|")
        preview_box = self.query_one("#preview-box", Static)
        if is_dir == "True":
            self.safe_update(preview_box.update, f"\n  [dim]Directory:[/] [green]{name}/[/]"); return
        try:
            self.safe_update(preview_box.update, f"\n  [dim]Loading preview...[/]")
            cfg = load_config(); ftp = connect(cfg)
            full_path = f"{self.current_path.rstrip('/')}/{name}"
            lines = []
            def callback(l):
                if len(lines) < 15: lines.append(l)
            ftp.retrlines(f"RETR {full_path}", callback); ftp.quit()
            content = "\n".join(lines); ext = os.path.splitext(name)[1].strip(".") or "txt"
            syntax = Syntax(content, ext, theme="monokai", line_numbers=True)
            self.safe_update(preview_box.update, syntax)
            self.log_message(f"Preview loaded: {name}")
        except Exception as e: self.safe_update(preview_box.update, f"\n  [red]Preview Error:[/] {e}")

    def action_toggle_panel(self):
        table = self.query_one(DataTable); sidebar = self.query_one("#sidebar")
        if self.focused and self.focused.id == "sidebar":
            table.focus(); self.log_message("Focus: File Manager")
        else:
            sidebar.focus(); self.log_message("Focus: Sessions")

    def action_open_shell(self):
        """Suspend TUI and launch the interactive Crow Shell."""
        self.log_message("Launching Crow Shell...")
        with self.suspend():
            # Create a dummy args object and call the existing shell command
            commands.cmd_shell(SimpleNamespace(id=self.current_id))
        
        # When shell exits, resume and refresh
        self.log_message("Resumed from Shell.")
        self.update_session_info()
        self.action_refresh()

    def action_edit_file(self):
        table = self.query_one(DataTable)
        if table.cursor_row is None: return
        row_keys = list(table.rows.keys())
        if table.cursor_row >= len(row_keys): return
        row_key_value = row_keys[table.cursor_row].value
        name, is_dir = row_key_value.split("|")
        if is_dir == "True": return
        full_path = f"{self.current_path.rstrip('/')}/{name}"
        suffix = os.path.splitext(name)[1] or ".txt"
        self.run_edit_orchestrator(name, full_path, suffix)

    @work(exclusive=True)
    async def run_edit_orchestrator(self, name: str, full_path: str, suffix: str):
        default_editor = "notepad" if os.name == "nt" else "nano"
        editor = os.environ.get("EDITOR", default_editor)
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp: tmp_path = tmp.name
        try:
            self.log_message(f"Downloading {name}...")
            await asyncio.to_thread(self.sync_download, full_path, tmp_path)
            self.log_message(f"Opening {editor}...")
            with self.suspend():
                subprocess.run([editor, tmp_path], shell=(os.name=="nt"))
            self.log_message("Uploading changes...")
            await asyncio.to_thread(self.sync_upload, name, full_path, tmp_path)
            os.unlink(tmp_path)
            self.log_message(f"SUCCESS: {name} updated.")
            self.action_refresh()
        except Exception as e:
            self.log_message(f"FAILED: {e}")
            if os.path.exists(tmp_path): os.unlink(tmp_path)

    def sync_download(self, remote: str, local: str):
        cfg = load_config(); ftp = connect(cfg)
        with open(local, "wb") as f: ftp.retrbinary(f"RETR {remote}", f.write)
        ftp.quit()

    def sync_upload(self, name: str, remote: str, local: str):
        with open(local, "r") as f: content = f.read()
        from crow.safeguards import validate_action, make_backup
        validate_action(remote, content, False)
        cfg = load_config(); ftp = connect(cfg); make_backup(ftp, remote)
        with open(local, "rb") as f: ftp.storbinary(f"STOR {remote}", f)
        ftp.quit()

    def handle_selection(self, row_key_value: str):
        if not row_key_value: return
        name, is_dir = row_key_value.split("|")
        if is_dir == "True":
            self.current_path = f"{self.current_path.rstrip('/')}/{name}"
            self.action_refresh(); self.query_one("#search-bar").value = ""

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        if event.row_key: self.handle_selection(event.row_key.value)

    def on_key(self, event):
        if self.focused and self.focused.id == "sidebar":
            sessions = list(load_sessions().keys()); current_idx = sessions.index(self.selected_id)
            if event.key == "up": self.selected_id = sessions[(current_idx - 1) % len(sessions)]; self.update_session_info()
            elif event.key == "down": self.selected_id = sessions[(current_idx + 1) % len(sessions)]; self.update_session_info()
            elif event.key == "enter":
                if self.current_id != self.selected_id:
                    self.current_id = self.selected_id; self.current_path = get_cwd(self.current_id)
                    self.update_session_info(); self.log_message(f"Loading session: {self.current_id}")
                    self.query_one(DataTable).focus(); self.action_refresh()
                else: self.query_one(DataTable).focus()

    def action_enter_item(self):
        if self.focused and self.focused.id == "sidebar": return
        table = self.query_one(DataTable)
        if table.cursor_row is not None:
            try:
                row_keys = list(table.rows.keys())
                if table.cursor_row < len(row_keys): self.handle_selection(row_keys[table.cursor_row].value)
            except: pass

    def action_parent_dir(self):
        if self.focused and self.focused.id == "sidebar": return
        if self.current_path != "/":
            parent = os.path.dirname(self.current_path.rstrip("/")) or "/"
            self.current_path = parent; self.action_refresh()

    def action_go_home(self):
        self.current_path = "/"; self.action_refresh()

    @on(Input.Changed, "#search-bar")
    def filter_files(self, event: Input.Changed):
        search_text = event.value.lower(); table = self.query_one(DataTable); table.clear()
        for item in self.all_items:
            if search_text in item["name"].lower():
                icon = get_icon(item["name"], item["is_dir"])
                display_name = Text(f"{icon} {item['name']}")
                if item["is_dir"]: display_name.stylize("bold green")
                table.add_row(display_name, item["size"], item["modified"], key=f"{item['name']}|{item['is_dir']}")

    def action_toggle_search(self):
        sb = self.query_one("#search-bar")
        if sb.has_class("-visible"): sb.remove_class("-visible"); self.query_one(DataTable).focus()
        else: sb.add_class("-visible"); sb.focus()

if __name__ == "__main__":
    app = CrowBrowser(); app.run()
