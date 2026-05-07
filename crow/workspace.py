import os

def create_ghost_file(path: str):
    """Creates a 0kb file and ensures parent directories exist."""
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, 'a'):
        os.utime(path, None)
