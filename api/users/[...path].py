import sys, os

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, "services", "user-service"))

from src.main import handler
