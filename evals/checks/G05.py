import sqlite3, tempfile, threading
import store
with tempfile.TemporaryDirectory() as d:
    path=d+'/db'; store.initialize(path)
    barrier=threading.Barrier(2); errors=[]
    def add():
        barrier.wait()
        try: store.create(path, 'same')
        except (sqlite3.IntegrityError, ValueError): pass
        except Exception as exc: errors.append(repr(exc))
    ts=[threading.Thread(target=add) for _ in range(2)]
    [t.start() for t in ts]; [t.join() for t in ts]
    assert not errors, errors
    with sqlite3.connect(path) as c:
        assert c.execute("select count(*) from items where key='same'").fetchone()[0] == 1
