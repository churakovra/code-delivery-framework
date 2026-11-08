import runpy,sys
from pathlib import Path
p=Path(sys.argv[1])
a=runpy.run_path(str(p/"app.py"))
assert a["preview"]()=="hello"
