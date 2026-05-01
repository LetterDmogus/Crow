import sys
from rich.console import Console
from rich.theme import Theme

# Define custom theme
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "session": "bold magenta",
})

console = Console(theme=custom_theme)

def die(msg: str, code: int = 1):
    console.print(f"[error]ERROR:[/] {msg}")
    sys.exit(code)

def ok(msg: str):
    console.print(f"[success]OK:[/] {msg}")

def info(msg: str):
    console.print(f"[info]INFO:[/] {msg}")
