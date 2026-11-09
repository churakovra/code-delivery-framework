import runpy, hashlib
from pathlib import Path
assert runpy.run_path("app.py")["greeting"]() == "hello"
assert hashlib.sha256(Path("test_app.py").read_bytes()).hexdigest() == '2087c1d4d5e024a6a90ef0fa4cb61239f81cc7ae96d18574b6623d74373547eb'
