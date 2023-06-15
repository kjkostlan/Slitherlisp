# Why such a lengthy AST? Can we instead translate it into a lispy format?
# The code is nested lists.
# TODO: this is a github project on it's own.
import ast, re
from . import symbol, lispy_simp, lispy_walk
symbol.sym_splat(__name__)

def translate_ast(X, tmp_level=0):
    # The meat of this module.
    #print('Stuff:', dir(X)) # body, type_ignores.
    ty = type(X)
    TR = lambda x: translate_ast(x, tmp_level)
    TR1 = lambda x: translate_ast(x, tmp_level+1)
    if ty == ast.Name:
        id = X.id
        if id.encode("ascii", "ignore").decode() != id:
            TODO # un-unicode.
        return Symbol(id)
    elif ty == ast.Attribute:
        return [Symbol('.-'+X.attr), TR(X.value)] # Also a Clojure idiomatic.
    elif ty == ast.Constant:
        return X.value # Literals.
    elif ty == ast.Subscript:
        return [INDEX, TR(X.value), TR(X.slice)]
    elif ty == ast.Slice:
        lo = X.lower; up = X.upper; st = X.step
        TODO
        TODO
    elif ty == ast.Expr: # Not sure what this is.
        return TR(X.value)
    elif ty==ast.If:
        out = [Symbol('if'), TR(X.test), [DO]+[TR(bi) for bi in X.body]]
        if len(X.orelse)>0:
            out.append([DO]+[TR(elsi) for elsi in X.orelse])
        return out
    elif ty == ast.IfExp: # Two types of if statements!?
        #print('If exp:', X, X.__dict__)
        if type(X.body) is list:
            out = [Symbol('if'), TR(X.test), [DO]+[TR(bi) for bi in X.body]]
        else:
            out = [Symbol('if'), TR(X.test), TR(X.body)]
        if type(X.orelse) is not list:
            out.append(TR(X.orelse))
        elif len(X.orelse)>0:
            out.append([DO]+[TR(bi) for bi in X.orelse])
        return out
    elif ty == ast.While:
        out = [Symbol('while'), TR(X.test), [DO]+[TR(bi) for bi in X.body]]
        if len(X.orelse)>0:
            out.append([DO]+[TR(bi) for bi in X.orelse])
        return out
    elif ty is ast.Compare:
        if len(X.ops)>1:
            raise Exception('How do multible X.ops in ast.Compare work?')
        if len(X.comparators)>1:
            raise Exception('How do multible X.comparators in ast.Compare work?')
        return [TR(X.ops[0]), TR(X.left), TR(X.comparators[0])]
    elif ty is ast.BinOp:
        return [TR(X.op), TR(X.left), TR(X.right)]
    elif ty is ast.BoolOp:
        return [TR(X.op)]+[TR(v) for v in X.values]
    elif ty is ast.Assign:
        t0 = TR(X.targets[0])
        val = TR(X.value)
        out = [Symbol('='), t0, val]
        if len(X.targets)>1: # Multible a = b = c
            pieces = []
            for t in X.targets[1:]: # multi equal.
                pieces.append([Symbol('='), TR(t), val])
            return [SPLICE]+[out]+pieces
        return out
    elif ty is ast.Add:
        return Symbol('+')
    elif ty is ast.And:
        return Symbol('and')
    elif ty is ast.Mult:
        return Symbol('*')
    elif ty is ast.Starred:
        return [Symbol('*'), TR(X.value)]
    elif ty is ast.Eq:
        return Symbol('==')
    elif ty is ast.Gt:
        return Symbol('>')
    elif ty is ast.Lt:
        return Symbol('<')
    elif ty is ast.Break:
        return Symbol('break')
    elif ty is ast.NotEq:
        return Symbol('!=')
    elif ty is ast.List:
        return [LIST]+[TR(elt) for elt in X.elts]
    elif ty is ast.ListComp: # One of the most complex cases.
        #print('Elt:', X.elt.__dict__, type(X.elt))
        #print('ELT pieces:', X.elt.left.__dict, X.elt.op.__dict, X.elt.right.__dict)
        #print('Elt is:', X.elt, type(X.elt))
        gen_list = []
        for gen in X.generators:
            gencode = [MOD, TR(gen.target), TR(gen.iter)]+[TR(ifst) for ifst in gen.ifs]
            gen_list.append(gencode)
        return [LISTCOMP, TR(X.elt)]+gen_list
        #print('Generators:', type(X.generators[0]), X.generators[0].__dict__)
    elif ty is ast.DictComp:
        gen_list = []
        for gen in X.generators:
            gencode = [MOD, TR(gen.target), TR(gen.iter)]+[TR(ifst) for ifst in gen.ifs]
            gen_list.append(gencode)
        return [DICTCOMP, TR(X.key), TR(X.value)]+gen_list
    elif ty is ast.Call: # One of the most complex cases.
        if type(X.func) is ast.Name:
            fnname = [Symbol(X.func.id)]
        elif type(X.func) is ast.Attribute:
            if type(X.func.value) is ast.Constant: # 'foo bar'.split(' ')
                fnname = [Symbol('.'+X.func.attr), TR(X.func.value)]
            else:
                fnname = [Symbol('.'+X.func.attr), Symbol(X.func.value.id)] # Very Clojure-like here.
        args = [TR(a) for a in X.args]
        kwds = []
        for kwd0 in X.keywords:
            if kwd0.arg is None: # This seems a bit out of place.
                kwds.append([Symbol('**'), TR(kwd0.value)])
            else:
                kwds.append([Symbol('='), Symbol(kwd0.arg), TR(kwd0.value)])
        return fnname+args+kwds
    elif ty is ast.FunctionDef: # Is this the most complicated one?
        arg_piece = [TUPLE]+[Symbol(a.arg) for a in X.args.args] #translate_ast(bodyi.args)
        #print('Def args stuff:', X.args.__dict__)
        if X.args.vararg is not None:
            arg_piece.append([Symbol('*'), Symbol(X.args.vararg.arg)])
        kwds = []
        for kwd0 in X.args.kwonlyargs:
            if kwd0.arg is None: # This seems a bit out of place.
                kwds.append([Symbol('**'), TR(kwd0.value)])
            else:
                kwds.append([Symbol('='), Symbol(kwd0.arg), TR(kwd0.value)])
        arg_piece = arg_piece+kwds
        body_piece = [DO]+[TR(bi) for bi in X.body]
        return [Symbol('def'), Symbol(X.name), arg_piece, body_piece]
    elif ty is ast.ClassDef:
        bases_kwds = [TUPLE]+[Symbol(b.id) for b in X.bases]
        for k in X.keywords: # Not sure if it works this way for ClassDef...
            for kwd0 in X.keywords:
                if kwd0.arg is None: # This seems a bit out of place.
                    bases_kwds.append([Symbol('**'), TR(kwd0.value)])
                else:
                    bases_kwds.append([Symbol('='), Symbol(kwd0.arg), TR(kwd0.value)])
        return [Symbol('class'), Symbol(X.name)]+[bases_kwds]+[[DO]+[TR(bi) for bi in X.body]]
    elif ty is ast.Return:
        return [Symbol('return'), TR(X.value)]
    elif ty is ast.Module:
        return [DO]+[TR(bi) for bi in X.body]
    elif ty is ast.Pass:
        return SPLICE
    else:
        if type(X) is list:
            raise Exception('X is a list. We should have called TR on each element of said list, not the whole list (bug in this code).')
        print('Need to handle this ast type:', X, X.__dict__)
        raise Exception('Please add code in this switchyard to handle this type: '+str(ty))

def python_ast2vanilla(X):
    # Recursive on vanilla AST. No special lispification.
    if type(X) is str: # You can also put a string inside.
        X = ast.parse(X)
    def class_str(Y):
        return str(type(Y)).replace("<class '",'').replace("'>",'')
    def is_ast_ty(Y):
        ty = class_str(Y)
        return (ty+'    ')[0:4]=='ast.'
    blocklist = {'ctx', 'lineno', 'col_offset', 'end_lineno', 'end_col_offset', 'type_comment', 'type_ignores'}
    attrs = set(X.__dict__.keys())-blocklist
    attrs = list(attrs); attrs.sort()
    pieces = {}
    for a in attrs:
        Xa = getattr(X,a)
        if type(Xa) is list:
            pieces[a] = [python_ast2vanilla(ai) for ai in Xa]
        elif is_ast_ty(Xa):
            pieces[a] = python_ast2vanilla(Xa)
        else:
            pieces[a] = str(Xa)
    pieces['type'] = class_str(X)
    return pieces

def treetxt2tree(txt, all_strings_are_easy=False):
    # Inverse of str(tree).
    #   Note: txt is NOT python code; that would be read_string.
    # Mainly used to manually enter trees.
    if '"' in txt or "'" in txt and not all_strings_are_easy:
        raise Exception('String literals will create problems if they have (){}[]:, or spaces in them. Set all_strings_are_easy=True to suppress this error.')

    def trim1(txt1):
        txt1 = txt1.strip()
        for c in [',',':']:
            if len(txt1)>0:
                if txt1[0]==c:
                    txt1 = txt1[1:]
            if len(txt1)>0:
                if txt1[-1]==c:
                    txt1 = txt1[0:-1]
        return txt1.strip()

    if '(' not in txt and '[' not in txt and '{' not in txt: # Leaf-level.
        try:
            return int(txt)
        except ValueError:
            pass
        try:
            return float(txt)
        except ValueError:
            pass
        if '"' in txt or "'" in txt:
            return txt

        tmap = {'LIST':LIST, 'TUPLE':TUPLE, 'LISTCOMP':LISTCOMP, 'DICT':DICT, 'DICTCOMP':DICTCOMP, 'SET':SET, 'SPLICE':SPLICE,'LOCAL':LOCAL,'NONLOCAL':NONLOCAL, 'DO':DO, 'INDEX':INDEX, 'MOD':MOD}
        return tmap.get(txt, Symbol(txt))

    txt = trim1(txt)

    bracket = txt[0]
    txt = txt[1:-1] # remove the [] and work wish the pieces.

    n = len(txt)
    start_ixs = [0]
    lev = 0

    for i in range(n):
        c = txt[i]
        if c==']' or c==')' or c=='}':
            lev = lev-1
        if lev==0 and (c ==' ' or c=='\t' or c=='\n' or c==',' or c==':'):
            start_ixs.append(i+1)
        if c=='[' or c=='(' or c=='{':
            lev = lev+1

    start_ixs.append(n)
    pieces = [trim1(txt[start_ixs[i]:start_ixs[i+1]]) for i in range(len(start_ixs)-1)]
    pieces1 = []
    for p in pieces:
        if len(p)>0:
            pieces1.append(p)
    pieces2 = [treetxt2tree(piece, True) for piece in pieces1]

    if bracket=='{':
        pairs = []; ix = 0
        while ix<len(pieces2):
            pairs.append([pieces2[ix], pieces2[ix+1]])
            ix = ix+2
        return dict(zip(pairs))
    elif bracket=='[':
        return pieces2
    elif bracket=='(':
        return [TUPLE]+pieces2
    else:
        raise Exception("couldn't find bracket.")

def read_string(txt, pure_list=False):
    # The main function. pure_list can break down string literals.
    tree = translate_ast(ast.parse(txt))
    tree = lispy_simp.splice_spliced(tree)
    if pure_list:
        tree = py_translate.make_pure_list(tree)
    return tree
