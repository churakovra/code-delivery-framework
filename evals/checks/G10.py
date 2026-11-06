import formatter
assert formatter.active('  x ') == 'x'
assert not hasattr(formatter, 'unused')
