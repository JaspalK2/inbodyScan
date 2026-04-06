import sys, os

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, repo_root)
sys.path.insert(0, os.path.join(repo_root, 'services', 'scan-service'))

from src.main import handler
