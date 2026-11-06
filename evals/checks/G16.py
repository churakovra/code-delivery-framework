import app
app.cache.clear()
assert app.submit('a',1)==1
assert app.submit('a',2)==1
assert app.cache == {'a':1}
