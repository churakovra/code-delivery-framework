from migration import migrate
assert migrate([{'id':1}]) == [{'id':1, 'active':True}]
assert migrate([{'id':1,'active':False}]) == [{'id':1,'active':False}]
