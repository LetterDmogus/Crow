import os
from textual.widgets import Static, DataTable, Input, Tabs, Tab, ContentSwitcher
from textual.containers import Vertical, ScrollableContainer
from textual import on
from rich.text import Text
from rich.syntax import Syntax
from crow.tui.utils import get_icon, format_size
from crow.commands import parse_ftp_line
from crow.core import load_config, connect, load_sessions, get_cwd

class FilePanel(Vertical):
    """A reusable FTP file browser panel with its own integrated Tab Switcher."""
    
    def __init__(self, panel_id: str, session_id: str = "default", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.panel_id = panel_id
        self.session_id = session_id
        self.current_path = get_cwd(session_id)
        self.all_items = []
        self.can_focus = True
        self.viewing_file = False

    def compose(self):
        # Local Tab Switcher for this panel
        sessions = load_sessions()
        yield Tabs(*[Tab(sid, id=f"tab-{self.panel_id}-{sid}") for sid in sessions], id=f"tabs-{self.panel_id}")
        
        yield Static(f"PATH: {self.current_path}", id=f"title-{self.panel_id}", classes="panel-title")
        yield Input(placeholder="Search...", id=f"search-{self.panel_id}", classes="search-bar")
        
        with ContentSwitcher(initial=f"table-{self.panel_id}", id=f"switcher-{self.panel_id}"):
            table = DataTable(id=f"table-{self.panel_id}")
            table.add_columns("Name", "Size", "Modified")
            table.cursor_type = "row"
            yield table
            
            with ScrollableContainer(id=f"viewer-container-{self.panel_id}"):
                yield Static(id=f"viewer-{self.panel_id}")

    def set_session(self, session_id: str, path: str):
        self.session_id = session_id
        self.current_path = path
        self.show_table()
        self.update_title()

    def set_path(self, path: str):
        self.current_path = path
        self.show_table()
        self.update_title()

    def show_table(self):
        self.viewing_file = False
        self.query_one(f"#switcher-{self.panel_id}", ContentSwitcher).current = f"table-{self.panel_id}"
        self.query_one(DataTable).focus()

    def show_viewer(self, name: str, content: str):
        self.viewing_file = True
        import os
        ext = os.path.splitext(name)[1].strip(".") or "txt"
        syntax = Syntax(content, ext, theme="monokai", line_numbers=True)
        self.query_one(f"#viewer-{self.panel_id}", Static).update(syntax)
        self.query_one(f"#switcher-{self.panel_id}", ContentSwitcher).current = f"viewer-container-{self.panel_id}"
        self.query_one(f"#viewer-container-{self.panel_id}").focus()

    def update_title(self, last_refreshed: str = None):
        try:
            title_widget = self.query_one(f"#title-{self.panel_id}", Static)
            text = f"PATH: {self.current_path}"
            if last_refreshed:
                text += f" [dim](Refreshed: {last_refreshed})[/]"
            title_widget.update(text)
        except: pass

    def update_list(self, ftp_entries, last_refreshed: str = None):
        table = self.query_one(DataTable)
        table.clear()
        self.update_title(last_refreshed)
        self.all_items = []
        for line in ftp_entries:
            item = parse_ftp_line(line)
            if not item or item["name"].strip() in (".", ".."): continue
            self.all_items.append(item)
            icon = get_icon(item["name"], item["is_dir"])
            display_name = Text(f"{icon} {item['name']}")
            if item["is_dir"]: display_name.stylize("bold green")
            readable_size = format_size(item["size"])
            table.add_row(display_name, readable_size, item["modified"], key=f"{item['name']}|{item['is_dir']}")
