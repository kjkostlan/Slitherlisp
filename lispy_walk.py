# Query and navigation tools.
# This file will grow quite large!
from . import symbol
symbol.sym_splat(__name__)

###########################Non-recursive functions##############################

def to_ast1(tree):
    # Translates the outer level of tree back into an AST-like dict.
    # Various information (list may be added to). All keys are present but some can be none.
    #  TODO: make changes to this.
    #  'bodies' = Parts of the code that are ran normally.
    #  'conditional' = If True means bodies[0] will be the condition for bodies[1] vs bodies[2].
    #  'object' = The 'foo' in 'foo.bar' or x in x['y']. None if not using an object.
    #  'vars' = Which vars are created.
       # 'name' = String name.
       # 'default_ix' = Which body index is this vars default.
       # 'splat' = Is splatted. None, '*', or '**'. (we treat False '' and None all the same).
    #  'leaf' = None unless a leaf value (then everything else is None)
    #  'sym' = Original symbol.
    TODO 

def from_ast1(ast1_tree):
    # Undoes to_ast1.
    TODO

###########################Recursive query fns##################################

def sym_set(tree):
    # All symbols in tree.
    return TODO

def contains_flow_escapes(tree):
    # Does it have break, return, or throw statements which can break out of the highest level.
    # (applies at every level).
    if type(tree) is dict:
        return contains_flow_escapes(list(tree.values()))
    if type(tree) is set:
        return contains_flow_escapes(list(tree))
    if type(tree) is list or type(tree) is tuple:
        for branch in tree:
            if contains_flow_escapes(branch):
                return True
        return False
    if type(tree) is Symbol:
        return tree.value in ['break', 'return', 'throw']
    return False

def fname(tree):
    # Returns the string if the first element is a symbol, otherwise None.
    if type(tree) is list or type(tree) is tuple:
        if len(tree)>0:
            if type(tree[0]) is Symbol:
                return str(tree[0])
    return None

###########################Recursive modification fns, reversible##########################

def _branch_assign(x, var_name, top_level, null_threat_indicator):
    if type(x) is Symbol and (x.value=='break' or x.value=='try' or x.value=='throw'):
        return x # No change.
    elif type(x) is not list and type(x) is not tuple:
        return [Symbol('='), Symbol(var_name), x]
    elif x[0].value=='if' or x[0].value=='while' or x[0].value=='for':
        # Two branches, either could assign the value.
        x = x.copy()
        #if no_ifwhiles_yet: # Add a None on the outer level if or while.
        #   x = add_elses1(x)
        for o in range(2, len(x)):
            x[o] = _branch_assign(x[o], var_name, False, [False])
        if len(x)>3:
            null_threat_indicator[0] = False
        else:
            null_threat_indicator[0] = True
        return x
    elif x[0] is DO:
        # The last element sets it, unless breaks etc mess us up.
        # (adding a few extra assignmnets doesn't break the code correctness).
        x = x.copy()
        escs = [contains_flow_escapes(br) for br in x]
        i = len(x)-1
        null_threat_resolved = False
        while i>0:
            if escs[i] or i==len(x)-1 or escs[i+1] or not null_threat_resolved:
                threati = [False]
                x[i] = _branch_assign(x[i], var_name, False, threati)
                if not threati[0]:
                    null_threat_resolved = True
            if escs[i]: # Re-instate the null threat.
                null_threat_resolved = False
            i = i-1
        if not null_threat_resolved and top_level:
            return [DO, [Symbol('='), Symbol(var_name), Symbol(None)], x]
        return x
    elif x[0].value=='class' or x[0].value=='def': # Eval to the symbol itself.
        return [DO, x, [Symbol('='), Symbol(var_name), x[1]]]
    elif x[0].value=='=' or x[0].value==LOCAL or x[0].value==NONLOCAL:
        if type(x[1]) is Symbol:
            sym = x[1]
        else: # Stuff like a[1] = 0.
            sym = x[1][1]
            if type(sym) is not Symbol:
                raise Exception('Complicated = LHS what should we do here?')
        return [DO, x, [Symbol('='), Symbol(var_name), sym]]
    else: # Function call sets to the return value.
        return [Symbol('='), Symbol(var_name), x]

def branch_assign(x, var_name):
    # Adds assignments to var_name in x wherever it is needed.
    # This will make var_name evaluate to what x evaluates to under lisp-like rules.
    out = _branch_assign(x, var_name, True, [None])
    return out


def macro_expand(code, macro_dict, module=None):
    # Recursivly macro-expands code.
    # macro_dict maps Symbols to f(code, form).
    TODO
