import sys, os

# Go up 2 dirs from api/auth/ to reach the project root where
# services/ and shared/ live (per includeFiles in vercel.json)
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, "services", "auth-service"))

from src.main import handler
