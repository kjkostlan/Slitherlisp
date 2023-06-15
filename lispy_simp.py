# Simplifies our lispy trees.
# These functions are generally irreversible.
from . import symbol, lispy_walk
symbol.sym_splat(__name__)

###########################Small modification fns###############################

def _gsym(x, gensym_ix):
    if gensym_ix is None:
        return str(len(str(x))) # Using total len avoids nesting collisions.
    else:
        ix = gensym_ix[0]; gensym_ix[0] = gensym_ix[0]+1
        return ix

def add_elses1(x):
    # Add an else (with a None symbol). Use if ifs, fors, and whiles if they don't have them already.
    if len(x)==3:
        return x+[Symbol('None')]
    return x

def embed_returns1(fn_def):
    # Lisp doesn't use returns, but Python does.
    # Can we make things more lispy?
    TODO

def expand_listcomp1(listcomp_obj, gensym_ix=None):
    # Expands a listcomp to be in a for loop.
    # Use if there is lisp-homesickness inside the listcomp or your code anal tool needs it.
    # [... for ix in vec] => tmp = []; for ix in vec: TODO.
    ix = _gsym(listcomp_obj, gensym_ix)
    varname = chr(6293)+'LCOMP'+str(ix)
    TODO

def expand_dictcomp1(dictcomp_obj, gensym_ix=None):
    # Now for dict_comps.
    ix = _gsym(dictcomp_obj, gensym_ix)
    varnameK = chr(6286)+'DCOMPK'+str(ix)
    varnameV = chr(6286)+'DCOMPV'+str(ix)
    TODO

def unliteral_dict(dict, gensym_ix=None):
    #Returns a DO block which makes an empty dict and adds kv pairs.
    # The last element of the output is the tmp var Symbol.
    out = [DO]
    ix = _gsym(dictcomp_obj, gensym_ix)
    varname = chr(6295)+'DICT'+str(ix)
    TODO
    out.append(Symbol(varname))

def unliteral_list(dict, gensym_ix=None):
    # Same idea as unliteral_dict, also wrapped by a DO block.
    TODO

def unliteral_set(set, gensym_ix=None):
    # Based on unliteral_list.
    TODO

###########################Default simplifications##############################

def simplify_var_assignments(tree, only_unicode=False):
    # tmp = a; c = tmp can be simplified.
    # In this case "tmp" is a symbol that can be replaced by a.
    # only_unicode = Only remove unicode vars, in case non-unicode vars need to be axcessed externally.
    TODO # Problems with this fn: order of var declaration.
    #Don't think needed: tree = py_sunshine.unicode_scope_rename(tree)
    tree = copy.deepcopy(tree)

    # Eqivalent symbols:
    eq_symbol_pairs = [] # [[a=b],[c=d],...]
    def fill_eq_syms(x):
        if type(x) is list or type(x) is tuple:
            [fill_eq_syms(xi) for xi in x]
            if x[0].value=='=' or x[0]==LOCAL or x[0]==NONLOCAL:
                if type(x[1]) is Symbol and type(x[2]) is Symbol:
                    eq_symbol_pairs.append([x[1].value,x[2].value])
        if type(x) is dict:
            fill_eq_syms(list(x.values()))
        if type(x) is set:
            fill_eq_syms(list(x))
    fill_eq_syms(tree)

    # Build a dictionary remap:
    remap = {}
    for pair in eq_symbol_pairs:
        if not only_unicode or pair[1].encode("ascii", "ignore").decode() != pair[1]:
            if pair[1] not in remap:
                target = pair[0]
                n = len(remap); k = 0
                while target in remap:
                    target=remap[target]
                    k=k+1
                    if k==n+1:
                        raise Exception('Circles why?')
                remap[pair[1]] = target

    #Apply the remap:
    def apply_remap(x):
        if type(x) is Symbol:
            if x.value in remap:
                x.value = remap[x.value]
            return x
        if type(x) is list or type(x) is tuple:
            return [apply_remap(xi) for xi in x]
        if type(x) is dict:
            for k,v in x.items():
                x[k] = apply_remap(x[v])
            return x
        if type(x) is set:
            return set(apply_remap(list(x)))
        return x
    tree = apply_remap(tree)

    def a_eq_a(x):
        out = False
        if type(x) is list or type(x) is tuple:
            if x[0].value=='=' or x[0]==LOCAL or x[0]==NONLOCAL:
                if x[1]==x[2]:
                    out = True
        return out

    def remove_a_eq_a(x):
        if type(x) is list or type(x) is tuple:
            x1 = [remove_a_eq_a(xi) for xi in x]
            x2 = []
            for xi in x1:
                if not a_eq_a(xi):
                    x2.append(x1)
            return x2
        if type(x) is dict:
            for k,v in x.items():
                x[k] = remove_a_eq_a(x[v])
            return x
        if type(x) is set:
            return set(remove_a_eq_a(list(x)))
    tree = remove_a_eq_a(tree)

    return tree

def reduce_nesting(tree):
    # Removes superflous nesting. TODO: more cases.
    if type(tree) is list or type(tree) is tuple:
        tree1 = [reduce_nesting(branch) for branch in tree]
        if len(tree1)==2 and tree1[0] == DO:
            return tree1[1]
        if tree1[0] != DO:
            return tree1
        tree2 = [] # Nested DO compression.
        for t1 in tree1:
            if (type(t1) is list or type(t1) is tuple) and t1[0]==DO:
                tree2 = tree2+t1[1:]
            else:
                tree2.append(t1)
        return tree2
    elif type(tree) is dict:
        return dict(zip(tree.keys(), [reduce_nesting(tree[k]) for k in tree.keys()]))
    elif type(tree) is set:
        return set([reduce_nesting(branch) for branch in tree])
    else:
        return tree

def splice_spliced(tree):
    # Putting SPLICE at the beginning of a list will cause this to splice it into the overlying list.
    if type(tree) is list or type(tree) is tuple:
        out = []
        for ti in tree:
            if ti==SPLICE:
                continue
            if lispy_walk.fname(ti)==SPLICE.value:
                out = out+ti[1:]
            elif lispy_walk.fname(ti)==DO.value and len(ti)==1:
                continue # Empty DO.
            else:
                out.append(ti)
        return [splice_spliced(ti) for ti in out]
    elif type(tree) is dict:
        return dict(zip(tree.keys(), [splice_spliced(ti) for ti in tree.values()]))
    elif type(tree) is set:
        return set([splice_spliced(ti) for ti in tree])
    return tree

def simplify(tree):
    tree = splice_spliced(tree)
    #tree = simplify_var_assignments(tree, True)
    tree = reduce_nesting(tree)
    return tree

###########################Other simplifications##############################

def returns_at_end(tree):
    # Makes all functions return whatever they return at the very end.
    # May affect performance (Not sure about this!).
    # WARNING: this will be hard work.
    TODO

def varname_munge(tree, prepend='x', rename_outer_scope=True):
    # Renames all vars, in the order they are defined, to x0, x1, x2, etc.
    # Mainly a debug tool to check for equivalence.
    #   Tuples to lists also as a free bonus.
    TODO