from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Log
from textual.containers import Horizontal
from crow.tui.widgets.doctor import DoctorWidget

class DashboardApp(App):
    CSS = """
    Screen { background: transparent; }
    #doctor { width: 40%; border-right: solid $primary; padding: 1; }
    #activity-log { width: 60%; background: transparent; }
    .section-title { text-style: bold; color: $accent; margin-bottom: 1; }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("f", "fix_workspace", "Fix Workspace"),
        ("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield DoctorWidget(id="doctor")
            yield Log(id="activity-log")
        yield Footer()

    def on_mount(self):
        from crow.workspace import check_integrity, fix_integrity
        self.log_message("Dashboard Started.")
        if not check_integrity()["workspace"]:
            fix_integrity()
            self.notify("Workspace skeleton restored!")
            self.query_one(DoctorWidget).update_status()

    def log_message(self, msg: str):
        self.query_one("#activity-log", Log).write_line(f"> {msg}")

    def action_fix_workspace(self):
        from crow.workspace import fix_integrity
        fix_integrity()
        self.query_one(DoctorWidget).update_status()
        self.notify("Workspace fixed.")
        self.log_message("Integrity fix applied.")

    def action_refresh(self):
        self.query_one(DoctorWidget).update_status()
        self.log_message("Status refreshed.")

if __name__ == "__main__":
    app = DashboardApp()
    app.run()
