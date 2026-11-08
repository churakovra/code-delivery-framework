import runpy,sys
from pathlib import Path
p=Path.cwd()
assert runpy.run_path(str(p/"app.py"))["greeting"]()=="hello"
