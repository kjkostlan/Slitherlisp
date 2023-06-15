from . import lispy_read, tree_translate, py_write, sunshine, symbol, lispy_simp
symbol.sym_splat(__name__)


def _alltrue(x):
    for xi in x:
        if not xi:
            return False
    return True

def _pleasework(x, msg_fail):
    if x:
        return True
    else:
        print(msg_fail)
        return False

# TODO: splice_spliced

def test_scratchpad():

    code = '''
def f(x):
    y = y1 = x*x
    return y*x
'''

    code = '''
[x if x != "banana" else "orange" for x in fruits]
'''

    code = '''
[x+1 for x in user_data if x.isdigit()]
'''

    code1 = '''
y = 1
[x+y for x in user_data]
def a(x):
    def foo(bar):
        baz = 1
        baz+2
        foo(x)
'''

    code = '''
bar(); foo.bar(); foo.bar(a,b,[c])
'''

    code = '''
x = 2
x = x+20
y = x+12
'''

    tree = lispy_read.read_string(code1)
    tree = py_sunshine.unicode_scope_rename(tree)

    print('Tree is:', tree)

    return False
#tree_translate.name_munge

def test_read():
    # Read_string played off against lispy_read.treetxt2tree
    read_string = lispy_read.read_string
    #treetxt2tree
    tests = []

    tests.append(len(str(lispy_read.treetxt2tree('[if, [== x 2],[= out 3]]')))>16) # Dump null check.
    tests.append(len(str(lispy_read.treetxt2tree('[foo]')))<24) # Dump null check.

    def testpair(code_txt, tree_txt, printy=False, ok_to_use_str_literals=False):
        #print('Gold vs green:', tree_gold, tree_green)
        if type(tree_txt) is str:
            tree_gold = lispy_read.treetxt2tree(tree_txt, ok_to_use_str_literals)
        else:
            tree_gold = tree_txt
        tree_green = lispy_simp.simplify(read_string(code_txt))

        if printy:
            print('Gold vs green:\n', '', tree_gold, '\n ', tree_green)
        tests.append(str(tree_gold)==str(tree_green))

    code_txt = '''
if x==2:
    out = 3
'''
    tree_txt = '[if, [== x 2],[=   out 3]]'
    testpair(code_txt, tree_txt)

    code_txt = '''
if x==2:
    out = 3
else:
    out = 4
'''
    tree_txt = '[if [== x 2] [= out 3] [= out 4]]'
    testpair(code_txt, tree_txt)

    code_txt = '''
if x==2:
    out = 3
elif x==3:
    out = 4
elif x==5:
    out = 6
'''
    tree_txt = '[if [== x 2] [= out 3] [if [== x 3] [= out 4] [if [== x 5] [= out 6]]]]'
    testpair(code_txt, tree_txt) # Elif becomes nested ifs.

    # TODO generators>1 length: [int(i) for sublist in list_of_lists for i in sublist]

    code_txt = '''
[y+123 for y in [1,2,4]]
[z for yy in the_array if yy>2 if zz>3]
[x if x != 123 else 456 for x in fruits]
[int(i) for sublist in list_of_lists for i in sublist]
'''
    tree_txt = '[DO, [LISTCOMP, [+, y, 123], [MOD, y, [LIST, 1,2,4]]] '
    tree_txt = tree_txt+ ',[LISTCOMP, z, [MOD yy, the_array, [> yy 2], [> zz 3]]]'
    tree_txt = tree_txt+ ',[LISTCOMP, [if [!= x 123] x 456] [MOD x fruits]]'
    tree_txt = tree_txt+ ',[LISTCOMP, [int i] [MOD sublist list_of_lists] [MOD i sublist]]]'

    testpair(code_txt, tree_txt, False)

    code_txt = '''
square_dict = {num: num*num for num in range(1, 11)}
'''
    tree_txt = '[= square_dict [DICTCOMP num, [* num, num], [MOD num [range 1 11]]]]'


    testpair(code_txt, tree_txt, False)



    code_txt = '''
easyTask()
medTask(a,b,c)
medTask(a,b,c=1,d=3+4)
'''
    tree_txt = '[DO, [easyTask], [medTask a b c], [medTask a b [= c 1] [= d [+ 3 4]]]]'
    testpair(code_txt, tree_txt, False)

    code_txt = '''
hardTask(a, *foo, **dfoo)
'''

    tree = [Symbol('hardTask'), Symbol('a'),[Symbol('*'), Symbol('foo')], [Symbol('**'), Symbol('dfoo')]]
    testpair(code_txt, tree, False)

    code_txt = '''
foo.bar(a,b,c)
'''
    tree_txt = '[.bar foo a b c]'
    testpair(code_txt, tree_txt, False)

    code_txt = "'worlds-apart'.split('-')"
    tree = [Symbol('.split'), 'worlds-apart', '-']
    testpair(code_txt, tree, False)


    code_txt = '''
def xyz():
    return 2
def foo(bar, baz):
    bar = bar+1
    return bar+1
def bar(*splatty):
    return baz+10
    '''
    tree_txt = '''[DO [def xyz [TUPLE] [return 2]]
                    [def foo [TUPLE bar baz] [DO [= bar [+ bar 1]] [return [+ bar 1]]]]
                    [def bar [TUPLE [* splatty]] [return [+ baz 10]]]
     ]'''
    testpair(code_txt, tree_txt, False)

    code_txt = '''
class Foo:
    def __init__(self):
        self.bar = 123

class Bar(Foo):
    pass

class Baz(Foo, Bar):
    x = 1
    y = 2
'''

#    print('AST:',lispy_read.python_ast2vanilla(
#    '''
#class Foo:
#    def __init__(self):
#        self.bar = 123
#    '''
#    )['body'][0])

    tree_txt = '''[DO
[class Foo [TUPLE] [def __init__ [TUPLE self] [= [.-bar self] 123]]]
[class Bar [TUPLE Foo]]
[class Baz [TUPLE Foo Bar] [DO [= x 1] [= y 2]]]
     ]'''
    testpair(code_txt, tree_txt, False)

    code_txt = '''
z = c['foo']
y = x[2][3]
'''

    tree_txt = '''
[DO
[= z [INDEX c 'foo']]
[= y [INDEX [INDEX x 2] 3]]
]
'''
    testpair(code_txt, tree_txt, True, True)


    code_txt = '''
x[0:2] = -1
x[1:] = -2
'''

    tree_txt = '''
[DO [=]]
'''

    testpair(code_txt, tree_txt, True)


    TODO # array indexing and slicing.

    TODO # list, dict, set literals.

    TODO # Decorators.

    TODO # 'foo%s%s'%('bar','baz') and related string interpolation.

    TODO # While loops (move this up, just below if statements).

    TODO # MORE to thinkk aobut.
    print('Tests test_read:', tests)

    return _alltrue(tests)

def test_expand_listdictcomp():
    return False

def test_value_split():
    # Tests splitting code into a "body" and "output".
    # Allows making outputs of large bodies of code.
    TODO
    return False

def test_extern_bulky():
    py_write.treetxt2tree(txt)
    # Tests the extern bulky step.
    code = [DO, [Symbol('='), Symbol('x'), 1], [Symbol('>'), Symbol('x'), 2]]
    #code = [Symbol('>'), [DO, [Symbol('='), Symbol('y'), 1], [Symbol('+'), Symbol('y'), Symbol(1)]], Symbol('b')]
    code = [Symbol('>'), [Symbol('='), Symbol('y'), 1], Symbol('b')]
    code = [Symbol('foo'), [Symbol('='), Symbol('y'), 1], Symbol('b')] # Fn calls allow a=b args.

    headers, code1 = py_write.extern_bulky(code)
    # Note: headers will have no DO prepend we need to add it!
    print('test_extern_bulky:', code, '->', headers, code1)
    return False

def test_dowrap_uncramp_branches1():

    read_string = lispy_read.read_string

    txt = '''
if a>z:
    x = 3
'''
    tree = read_string(txt)[1]
    #tree[1][1] = [DO, [Symbol('='), Symbol('y'), 1], Symbol('y')] # Replace the a.
    tree[1][1] = [Symbol('='), Symbol('y'), 1]

    tree1 = py_write.dowrap_uncramp_branches1(tree)
    print('test_dowrap_uncramp b4 vs aft:\n', ' ', tree, '\n  ', tree1)

    return False

def test_homesickness_treatment():
    # Tests cases where you need to outsource the code.
    read_string = lispy_read.read_string

    code = '''
if a>b:
    x = 3
'''
    tree = read_string(code)
    tree[1][1][1] = [Symbol('='), Symbol('y'), Symbol(1)] # Replace the a.

    print('Homesick code:', tree)
    tree1 = lispy_simp.simplify(py_write.extern_bulky_all(tree))
    print('Fixed code:', tree1)

    return False

def test_write():
    #pu_translate.core_blit(tree, indent=4)
    return False

def run_tests():
    out = []
    out.append(test_read())
    #out.append(test_expand_listdictcomp())
    #out.append(test_value_split())
    #out.append(test_extern_bulky())
    #out.append(test_dowrap_uncramp_branches1())
    #out.append(test_homesickness_treatment())
    #out.append(test_write())

    if len(out)<7:
        return False # testing only a few, need to uncomment more.

    for o in out:
        if not o:
            return False
    return True
