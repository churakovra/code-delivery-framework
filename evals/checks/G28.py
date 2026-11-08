import runpy,sys
from pathlib import Path
p=Path.cwd()
a=runpy.run_path(str(p/"app.py"))
assert a["preview"]()=="hello"
assert a["spacing"]==12
