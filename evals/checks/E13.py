import app
assert app.submit("key", "first") == {"value": "first"}
assert app.submit("key", "second") == {"value": "first"}
assert app.submit("other", "third") == {"value": "third"}
