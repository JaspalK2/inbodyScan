import sys, os

# Go up 3 dirs from frontend/api/<svc>/ to reach repo root
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, "services", "user-service"))

from src.main import handler
