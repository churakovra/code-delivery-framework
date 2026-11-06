import app, validators
from unittest.mock import patch
with patch.object(validators, 'valid_name', return_value=False) as check:
    assert app.register('any') == {'error': 'invalid name'}
    check.assert_called_once_with('any')
assert app.register('alice') == {'name': 'alice'}
