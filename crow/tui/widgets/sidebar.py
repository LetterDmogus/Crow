from textual.widgets import Static
from textual.containers import Vertical
from crow.core import load_sessions

class Sidebar(Vertical):
    """A focusable sidebar widget for sessions."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.can_focus = True

    def update_sessions(self, current_id, selected_id):
        sessions = load_sessions()
        info_text = "\n"
        for sid in sessions:
            marker = ""
            if sid == current_id: marker += "▶"
            if sid == selected_id: marker += " ❯"
            style = "bold cyan" if sid == selected_id else "white"
            info_text += f"  {marker:3} [{style}]{sid}[/]\n"
        self.query_one("#session-info", Static).update(info_text)
