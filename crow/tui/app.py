import os
import threading
import subprocess
import tempfile
import asyncio
import json
import time
from pathlib import Path
from types import SimpleNamespace

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, DataTable, Log, Input, Tabs, Tab, OptionList, ContentSwitcher
from textual.screen import ModalScreen
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual import work, on, events
from rich.text import Text
from rich.syntax import Syntax

from crow.core import connect, load_config, get_cwd, load_sessions
from crow import commands
from crow.tui.widgets.file_panel import FilePanel
from crow.tui.utils import get_icon, get_cached_entries, set_cached_entries

class EditorSelectionScreen(ModalScreen[str]):
    """Modal screen for selecting a text editor."""
    def compose(self) -> ComposeResult:
        with Vertical(id="editor-menu"):
            yield Static("OPEN WITH...", classes="section-title")
            yield OptionList(
                "Default (ENV)",
                "nano",
                "vim",
                "vi",
                "emacs",
                "code --wait",
                "subl -w",
                "micro",
                "notepad",
                id="editor-list"
            )

    @on(OptionList.OptionSelected)
    def on_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(str(event.option.prompt))

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.dismiss(None)

class Crowmander(App):
    """Crow TUI V1.8.3 - Dual Panel FTP Client."""
    
    CSS = """
    Screen { background: transparent; }
    
    #header-container {
        layout: horizontal;
        background: $primary;
        color: white;
        height: 1;
    }
    #header-title { width: 1fr; text-style: bold; padding: 0 1; color: $accent; }
    #header-clock { width: 25; text-align: right; padding: 0 1; color: $secondary; }

    #middle-container { height: 60%; }
    FilePanel { width: 50%; border: solid $primary; }
    FilePanel:focus-within { border: double $accent; background: $boost; }
    
    Tabs { height: 3; background: $boost; border-bottom: solid $primary; }
    
    .panel-title {
        text-align: center; width: 100%; color: $accent; text-style: bold;
        background: $primary; margin-bottom: 0; padding: 0;
    }
    .search-bar { display: none; margin: 0; border: none; height: 3; }
    .search-bar.-visible { display: block; }
    
    #bottom-container { height: 40%; border-top: solid $primary; }
    #log-panel { width: 50%; border-right: solid $primary; }
    #preview-panel { width: 50%; }
    .section-title {
        text-align: center; color: $secondary; text-style: italic;
        border-bottom: solid $primary;
    }
    DataTable { background: transparent; border: none; height: 1fr; }
    Log { background: transparent; color: $text-muted; }
    #preview-box { padding: 0 1; }

    #editor-menu {
        width: 40;
        height: 15;
        border: thick $accent;
        background: $boost;
        padding: 1;
        align: center middle;
    }
    #editor-menu .section-title { margin-bottom: 1; }

    #command-bar {
        display: none;
        background: $accent;
        color: $text;
        dock: bottom;
        height: 3;
        border: none;
    }
    #command-bar.-visible { display: block; }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("tab", "switch_panel", "Switch Panel"),
        ("r", "refresh_active", "Refresh"),
        ("space", "show_preview", "Preview"),
        ("o", "open_file", "Open"),
        ("d", "download_file", "Download (Get)"),
        ("u", "upload_file", "Upload (Put)"),
        ("e", "edit_file", "Edit"),
        (":", "toggle_command_bar", "Command"),
        ("/", "toggle_search", "Search"),
        ("n", "parent_dir", "Back"),
        ("m", "enter_item", "Forward"),
        ("ctrl+n", "prompt_mkdir", "Mkdir"),
        ("f2", "prompt_rename", "Rename"),
        ("delete,ctrl+x", "confirm_delete", "Delete"),
        ("backspace", "parent_dir", "Back"),
        ("h", "go_home", "Home"),
        ("escape", "close_all", "Close"),
    ]

    def __init__(self):
        super().__init__()
        self.sessions = load_sessions()
        self._main_thread = threading.get_ident()
        self.last_focused_panel_id = "left"

    def compose(self) -> ComposeResult:
        with Horizontal(id="header-container"):
            yield Static("CROWMANDER FTP MANAGER", id="header-title")
            yield Static("", id="header-clock")
        
        session_list = list(self.sessions.keys())
        left_sid = session_list[0] if len(session_list) > 0 else "default"
        right_sid = session_list[1] if len(session_list) > 1 else left_sid
        
        with Horizontal(id="middle-container"):
            yield FilePanel(panel_id="left", session_id=left_sid, id="left")
            yield FilePanel(panel_id="right", session_id=right_sid, id="right")
        
        with Horizontal(id="bottom-container"):
            with Vertical(id="log-panel"):
                yield Static("ACTIVITY LOG", classes="section-title")
                yield Log(id="cmd-log")
            with Vertical(id="preview-panel"):
                yield Static("PREVIEW", classes="section-title")
                yield Static("Press Space to preview...", id="preview-box")
        
        yield Input(placeholder="Command: mkdir <name> | rename <name> | del | put <path> | get | shell", id="command-bar")
        yield Footer()

    def on_mount(self) -> None:
        self.log_message("Crowmander Started.")
        self.set_interval(1, self.update_clock)
        for p_id in ["left", "right"]:
            self.refresh_panel(p_id)
        self.query_one("#table-left").focus()

    def update_clock(self) -> None:
        from datetime import datetime
        try:
            self.query_one("#header-clock", Static).update(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        except: pass

    def log_message(self, msg: str):
        try: self.query_one("#cmd-log", Log).write_line(f"> {msg}")
        except: pass

    def on_focus(self, event: events.Focus) -> None:
        node = event.control
        while node:
            if isinstance(node, FilePanel):
                self.last_focused_panel_id = node.panel_id
                break
            node = node.parent

    @on(Tabs.TabActivated)
    def handle_tab_activated(self, event: Tabs.TabActivated):
        tab_bar_id = event.tabs.id
        panel_id = "left" if tab_bar_id == "tabs-left" else "right"
        new_sid = event.tab.label.plain
        panel = self.query_one(f"#{panel_id}", FilePanel)
        if panel.session_id != new_sid:
            panel.set_session(new_sid, get_cwd(new_sid))
            self.refresh_panel(panel_id)

    def get_active_panel(self) -> FilePanel:
        node = self.focused
        while node:
            if isinstance(node, FilePanel):
                self.last_focused_panel_id = node.panel_id
                return node
            node = node.parent
        return self.query_one(f"#{self.last_focused_panel_id}", FilePanel)

    def action_switch_panel(self):
        target = "right" if self.last_focused_panel_id == "left" else "left"
        self.query_one(f"#{target} DataTable").focus()

    @work(exclusive=True, thread=True)
    def refresh_panel(self, panel_id: str, force_refresh: bool = False):
        panel = self.query_one(f"#{panel_id}", FilePanel)
        if not force_refresh:
            entries, last_refreshed = get_cached_entries(panel.session_id, panel.current_path)
            if entries is not None:
                self.log_message(f"[{panel.session_id}] Loaded {panel_id} from cache (Refreshed: {last_refreshed})")
                self.call_from_thread(panel.update_list, entries, last_refreshed)
                return
        
        self.log_message(f"[{panel.session_id}] Fetching {panel_id} from FTP...")
        try:
            cfg = load_config(); ftp = connect(cfg)
            entries = []
            ftp.retrlines(f"LIST {panel.current_path}", entries.append)
            ftp.quit()
            last_refreshed = set_cached_entries(panel.session_id, panel.current_path, entries)
            self.call_from_thread(panel.update_list, entries, last_refreshed)
        except Exception as e: self.log_message(f"Error {panel_id}: {e}")

    def action_toggle_command_bar(self):
        cb = self.query_one("#command-bar", Input)
        if cb.has_class("-visible"):
            cb.remove_class("-visible")
            self.get_active_panel().query_one(DataTable).focus()
        else:
            cb.add_class("-visible")
            cb.focus()

    @on(Input.Submitted, "#command-bar")
    def handle_command_submit(self, event: Input.Submitted):
        cmd_text = event.value.strip()
        cb = self.query_one("#command-bar", Input)
        cb.remove_class("-visible")
        cb.value = ""
        self.get_active_panel().query_one(DataTable).focus()
        if not cmd_text: return
        parts = cmd_text.split()
        cmd = parts[0].lower()
        args = parts[1:]
        if cmd == "mkdir" and args: self.run_mkdir_task(args[0])
        elif cmd == "rename" and args: self.run_rename_task(args[1] if len(args)>1 else args[0])
        elif cmd in ("del", "delete"): self.action_confirm_delete()
        elif cmd == "put" and args: self.run_upload_task(args[0])
        elif cmd in ("get", "download"): self.action_download_file()
        elif cmd == "shell": self.action_open_shell()
        else: self.log_message(f"Unknown command: {cmd}")

    def action_close_all(self):
        active = self.get_active_panel()
        if active.viewing_file: active.show_table()
        cb = self.query_one("#command-bar", Input)
        if cb.has_class("-visible"):
            cb.remove_class("-visible")
            active.query_one(DataTable).focus()

    def action_prompt_mkdir(self):
        cb = self.query_one("#command-bar", Input)
        cb.add_class("-visible"); cb.value = "mkdir "; cb.focus()

    def action_prompt_rename(self):
        active = self.get_active_panel()
        table = active.query_one(DataTable)
        if table.cursor_row is None: return
        row_keys = list(table.rows.keys())
        name, _ = row_keys[table.cursor_row].value.split("|")
        cb = self.query_one("#command-bar", Input)
        cb.add_class("-visible"); cb.value = f"rename {name} "; cb.focus()

    @work(exclusive=True, thread=True)
    def run_mkdir_task(self, name: str):
        active = self.get_active_panel()
        self.log_message(f"FTP REQ: MKD {name}")
        try:
            cfg = load_config(); ftp = connect(cfg)
            ftp.mkd(f"{active.current_path.rstrip('/')}/{name}")
            ftp.quit()
            self.log_message(f"FTP SUCCESS: Created directory {name}")
            self.refresh_panel(active.panel_id, force_refresh=True)
        except Exception as e: self.log_message(f"FTP ERROR: Mkdir failed: {e}")

    @work(exclusive=True, thread=True)
    def run_rename_task(self, new_name: str):
        active = self.get_active_panel()
        table = active.query_one(DataTable)
        if table.cursor_row is None: return
        row_keys = list(table.rows.keys())
        old_name, _ = row_keys[table.cursor_row].value.split("|")
        self.log_message(f"FTP REQ: RNFR {old_name} -> RNTO {new_name}")
        try:
            cfg = load_config(); ftp = connect(cfg)
            old_p = f"{active.current_path.rstrip('/')}/{old_name}"
            new_p = f"{active.current_path.rstrip('/')}/{new_name}"
            ftp.rename(old_p, new_p)
            ftp.quit()
            self.log_message(f"FTP SUCCESS: Renamed {old_name}")
            self.refresh_panel(active.panel_id, force_refresh=True)
        except Exception as e: self.log_message(f"FTP ERROR: Rename failed: {e}")

    def action_confirm_delete(self):
        active = self.get_active_panel()
        table = active.query_one(DataTable)
        if table.cursor_row is None: return
        row_keys = list(table.rows.keys())
        name, is_dir = row_keys[table.cursor_row].value.split("|")
        self.run_delete_task(name, is_dir == "True")

    @work(exclusive=True, thread=True)
    def run_delete_task(self, name: str, is_dir: bool):
        active = self.get_active_panel()
        self.log_message(f"FTP REQ: {'RMD' if is_dir else 'DELE'} {name}")
        try:
            cfg = load_config(); ftp = connect(cfg)
            full_path = f"{active.current_path.rstrip('/')}/{name}"
            if is_dir: ftp.rmd(full_path)
            else: ftp.delete(full_path)
            ftp.quit()
            self.log_message(f"FTP SUCCESS: Deleted {name}")
            self.refresh_panel(active.panel_id, force_refresh=True)
        except Exception as e: self.log_message(f"FTP ERROR: Delete failed: {e}")

    def action_upload_file(self):
        cb = self.query_one("#command-bar", Input)
        cb.add_class("-visible"); cb.value = "put "; cb.focus()

    @work(exclusive=True, thread=True)
    def run_upload_task(self, local_path: str):
        active = self.get_active_panel()
        path = Path(local_path)
        if not path.exists(): self.log_message(f"LOCAL: File not found: {local_path}"); return
        self.log_message(f"FTP REQ: STOR {path.name}")
        try:
            cfg = load_config(); ftp = connect(cfg)
            remote_p = f"{active.current_path.rstrip('/')}/{path.name}"
            with open(path, "rb") as f: ftp.storbinary(f"STOR {remote_p}", f)
            ftp.quit()
            self.log_message(f"FTP SUCCESS: Uploaded {path.name}")
            self.refresh_panel(active.panel_id, force_refresh=True)
        except Exception as e: self.log_message(f"FTP ERROR: Upload failed: {e}")

    def action_refresh_active(self):
        active = self.get_active_panel()
        if active.viewing_file: active.show_table()
        else: self.refresh_panel(active.panel_id, force_refresh=True)

    def action_open_file(self):
        active = self.get_active_panel()
        if active.viewing_file: return
        table = active.query_one(DataTable)
        if table.cursor_row is not None:
            row_keys = list(table.rows.keys())
            name, is_dir = row_keys[table.cursor_row].value.split("|")
            if is_dir == "False": self.run_open_task(name, active.current_path, active.panel_id)

    @work(exclusive=True, thread=True)
    def run_open_task(self, name: str, path: str, panel_id: str):
        panel = self.query_one(f"#{panel_id}", FilePanel)
        try:
            cfg = load_config(); ftp = connect(cfg)
            full_p = f"{path.rstrip('/')}/{name}"
            lines = []
            ftp.retrlines(f"RETR {full_p}", lines.append)
            ftp.quit(); self.call_from_thread(panel.show_viewer, name, "\n".join(lines))
        except Exception as e: self.log_message(f"Open failed: {e}")

    def action_download_file(self):
        active = self.get_active_panel()
        table = active.query_one(DataTable)
        if table.cursor_row is None: return
        row_keys = list(table.rows.keys())
        name, is_dir = row_keys[table.cursor_row].value.split("|")
        if is_dir == "False":
            self.run_download_task(name, f"{active.current_path.rstrip('/')}/{name}", str(Path.cwd()/name))

    @work(exclusive=False, thread=True)
    def run_download_task(self, name: str, rem, loc):
        try:
            self.sync_download(rem, loc)
            self.log_message(f"Downloaded: {name}")
        except Exception as e: self.log_message(f"Failed: {e}")

    def sync_download(self, remote, local):
        cfg = load_config(); ftp = connect(cfg)
        with open(local, "wb") as f: ftp.retrbinary(f"RETR {remote}", f.write)
        ftp.quit()

    def sync_upload(self, remote, local):
        with open(local, "r") as f: content = f.read()
        from crow.watchout import validate_action, make_backup
        validate_action(remote, content, False)
        cfg = load_config(); ftp = connect(cfg); make_backup(ftp, remote)
        with open(local, "rb") as f: ftp.storbinary(f"STOR {remote}", f)
        ftp.quit()

    def action_edit_file(self):
        active = self.get_active_panel()
        table = active.query_one(DataTable)
        if table.cursor_row is None: return
        row_keys = list(table.rows.keys())
        name, is_dir = row_keys[table.cursor_row].value.split("|")
        if is_dir == "False":
            full_p = f"{active.current_path.rstrip('/')}/{name}"
            def h(choice):
                if choice:
                    ed = os.environ.get("EDITOR", "nano") if choice=="Default (ENV)" else choice
                    self.run_edit_orchestrator(name, full_p, active.panel_id, ed)
            self.push_screen(EditorSelectionScreen(), h)

    @work(exclusive=True)
    async def run_edit_orchestrator(self, name: str, full_p: str, panel_id: str, editor: str):
        with tempfile.NamedTemporaryFile(suffix=os.path.splitext(name)[1], delete=False) as tmp:
            tmp_p = tmp.name
        try:
            await asyncio.to_thread(self.sync_download, full_p, tmp_p)
            with self.suspend(): subprocess.run(editor.split() + [tmp_p], shell=(os.name=="nt"))
            await asyncio.to_thread(self.sync_upload, full_p, tmp_p)
            os.unlink(tmp_p); self.refresh_panel(panel_id)
        except Exception as e: self.log_message(f"Edit failed: {e}")

    def action_show_preview(self):
        active = self.get_active_panel()
        table = active.query_one(DataTable)
        if table.cursor_row is not None:
            rk = list(table.rows.keys())[table.cursor_row].value
            self.run_preview_task(rk, active.current_path)

    @work(exclusive=True, thread=True)
    def run_preview_task(self, rk: str, path: str):
        name, is_dir = rk.split("|")
        pb = self.query_one("#preview-box", Static)
        if is_dir == "True": self.call_from_thread(pb.update, f"Dir: {name}"); return
        try:
            cfg = load_config(); ftp = connect(cfg); full_p = f"{path.rstrip('/')}/{name}"
            lines = []
            ftp.retrlines(f"RETR {full_p}", lambda l: lines.append(l) if len(lines)<15 else None)
            ftp.quit(); syntax = Syntax("\n".join(lines), os.path.splitext(name)[1].strip(".") or "txt", theme="monokai")
            self.call_from_thread(pb.update, syntax)
        except Exception as e: self.call_from_thread(pb.update, f"Error: {e}")

    @on(DataTable.RowSelected)
    def handle_navigation(self, event: DataTable.RowSelected):
        node = event.data_table
        while node and not isinstance(node, FilePanel): node = node.parent
        if node:
            name, is_dir = event.row_key.value.split("|")
            if is_dir == "True":
                node.set_path(f"{node.current_path.rstrip('/')}/{name}"); self.refresh_panel(node.panel_id)

    def action_enter_item(self):
        active = self.get_active_panel()
        table = active.query_one(DataTable)
        if table.cursor_row is not None:
            rk = list(table.rows.keys())[table.cursor_row].value
            name, is_dir = rk.split("|")
            if is_dir == "True":
                active.set_path(f"{active.current_path.rstrip('/')}/{name}"); self.refresh_panel(active.panel_id)

    def action_parent_dir(self):
        active = self.get_active_panel()
        if active.current_path != "/":
            active.set_path(os.path.dirname(active.current_path.rstrip("/")) or "/"); self.refresh_panel(active.panel_id)

    def action_open_shell(self):
        active = self.get_active_panel()
        with self.suspend(): commands.cmd_shell(SimpleNamespace(id=active.session_id))
        self.refresh_panel(active.panel_id)

    def action_go_home(self):
        active = self.get_active_panel(); active.set_path("/"); self.refresh_panel(active.panel_id)

    def action_toggle_search(self):
        active = self.get_active_panel(); sb = active.query_one(".search-bar")
        if sb.has_class("-visible"): sb.remove_class("-visible"); active.query_one(DataTable).focus()
        else: sb.add_class("-visible"); sb.focus()

if __name__ == "__main__":
    app = Crowmander(); app.run()
