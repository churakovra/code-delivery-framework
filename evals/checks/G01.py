from app import post
assert post('') == (400, {'error':'empty body'})
assert post('ok') == (200, {'received':'ok'})
