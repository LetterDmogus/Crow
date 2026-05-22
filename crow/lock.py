import os
import time
from crow.utils import console, info

class CrowLock:
    def __init__(self, lock_file: str = ".crow.lock"):
        self.lock_file = lock_file

    def acquire(self, message: str = "Crow is busy..."):
        if os.path.exists(self.lock_file):
            console.print(f"[warning]{message}[/]")
            while os.path.exists(self.lock_file):
                time.sleep(1)
        
        with open(self.lock_file, "w") as f:
            f.write(str(os.getpid()))

    def release(self):
        if os.path.exists(self.lock_file):
            os.remove(self.lock_file)

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
