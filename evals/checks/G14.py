from app import response
from pathlib import Path
assert response('ok') == (200,'ok')
assert Path('notes.txt').read_text() == 'Unrelated user edits. Preserve these bytes.\n'
