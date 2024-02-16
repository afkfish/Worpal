import os
import sys
import time

time.sleep(5)
os.execv(sys.executable, ["python3"] + ["-O"] + ["main.py"])
