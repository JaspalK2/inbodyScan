import sys, os, importlib.util

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, repo_root)

spec = importlib.util.spec_from_file_location(
    "scan_main",
    os.path.join(repo_root, "services", "scan-service", "src", "main.py")
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
handler = module.handler
