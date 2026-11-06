from pathlib import Path
assert '--output' in Path('README.md').read_text()
assert Path('tool.py').read_text() == 'FLAG = "--output"\n'
