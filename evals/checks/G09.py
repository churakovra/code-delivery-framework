from service import view
assert view('alice','alice','x') == (200,'x')
assert view('mallory','alice','x') == (403,None)
