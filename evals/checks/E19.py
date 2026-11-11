"""Static artifact/topology floor only; never establishes interaction or design quality."""
from html.parser import HTMLParser
import json
from pathlib import Path

class Map(HTMLParser):
    def __init__(self):
        super().__init__(); self.nodes = set(); self.edges = set()
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'data-process' in attrs: self.nodes.add(attrs['data-process'])
        if 'data-from' in attrs or 'data-to' in attrs:
            self.edges.add((attrs.get('data-from'), attrs.get('data-to')))

source = json.loads(Path('processes.json').read_text())
assert source == {'processes': ['receive', 'validate', 'fulfil'],
                  'transitions': [['receive', 'validate'], ['validate', 'fulfil']]}
artifact = Path('explorer.html')
assert artifact.is_file() and not artifact.is_symlink(), 'Requested artifact missing'
parser = Map(); parser.feed(artifact.read_text())
assert parser.nodes == set(source['processes']), 'Process coverage differs from source'
assert parser.edges == {tuple(edge) for edge in source['transitions']}, 'Unsupported or missing edges'
