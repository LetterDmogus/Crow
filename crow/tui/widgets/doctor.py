from textual.widgets import Static, Button
from textual.containers import Vertical
from crow.workspace import check_integrity, fix_integrity

class DoctorWidget(Vertical):
    def compose(self):
        yield Static("DASHBOARD DOCTOR", classes="section-title")
        yield Static("Status: Scanning...", id="doctor-status")
        yield Button("FIX WORKSPACE", id="fix-btn", variant="primary")

    def on_mount(self):
        self.update_status()

    def update_status(self):
        res = check_integrity()
        status_text = "\n".join([f"{k.upper()}: {'✅' if v else '❌'}" for k, v in res.items()])
        self.query_one("#doctor-status", Static).update(status_text)
