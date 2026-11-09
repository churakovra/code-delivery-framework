import app
for value in (None, 42, "", " alice", "alice "):
    assert app.register(value) == {"error": "invalid name"}, repr(value)
assert app.register("alice") == {"name": "alice"}
