from app import post
assert post("") == (422, {"error":"empty"})
assert post("ok") == (200,{"received":"ok"})
