# Blit Python code.
# Not-a-lisp means we have to vomit variable definitions embeded deeply.
import numpy as np # NOT used for speedup, but has other nice functions.
import copy
from . import symbol
symbol.sym_splat(__name__)

def _is_asgn(code):
    # Runs an in-place simplification step.
    is_eq = False
    if '=' in str(code):
        code1 = py_translate.simplify(code) # remove superflous do statements.
        del code[:];
        for c in code1: # inplace
            code.append(c)
        if ((type(code) is list) or type(code) is tuple) and code[0] == Symbol('='):
            is_eq = True
    return is_eq

############################# Detecting bulky code #############################

def outer_level_bulky(code):
    # IS the outer level bulky?
    if type(code) is list or type(code) is tuple: # This-level bulky cases.
        if len(code)==0:
            return False
        bulkies = {'def','class','for','while','=','try','catch','raise','break','return'} # Note: if is *not bulky* since inline if statments can be nested.
        if code[0].value in bulkies:
            return True # Note: there *are* nonbulky ifs but that is more nuanced.
        if code[0]==MOD:
            return False
        if code[0]==LOCAL or code[0]==NONLOCAL:
            return True # All forms of = are bulky.
        if (code[0]==DO or code[0]==SPLICE) and len(code)>2:
            return True # DO with more than one statement inside.
        if (code[0]==DO or code[0]==SPLICE) and len(code)==2: # Single element.
            return outer_level_bulky(code[1])
    return False

def outer_bulky_path(code, root_path):
    # The deepest path that contains all the bulky code.
    # None if not bulky, [] if the code itself has an if, =, etc.
    if outer_level_bulky(code):
        return []
    kys = None
    if type(code) is dict:
        kys = list(code.keys()); kys.sort()
    elif type(code) is set:
        kys = list(code); kys.sort()
    elif type(code) is list or type(code) is tuple:
        kys = list(range(len(code)))
    if kys is not None: # Big recursive step.
        phs = [outer_bulky_path(code[k], root_path+[k]) for k in kys]
        out = None
        for ph in phs:
            if ph is not None and out is not None:
                return [] # Multible bulky paths.
            elif ph is not None:
                out = ph
        return out
    elif type(code) is Symbol and code.value in {'break', 'return'}:
        return [] # I guess these are bulky, it would be unusualy to implement them.
    else:
        return None

def is_bulky(code):
    # Is a form bulky.
    #  x = a*here+b.
    #  Non-bulky forms can fit in the 'here'.
    # This function searches recursivly.
    # Can we fit in this tiny space here?
      # x = a+here
    return outer_bulky_path(code,[]) is not None

def is_simple_eq(x):
    # a=b can fit in fn calls or fn defs, but not just anywhere.
    if type(x) is not list:
        return False
    if len(x) !=3:
        return False
    if x[0].value != '=':
        return False
    if type(x[1]) is not Symbol:
        return False
    return is_bulky(x[2])

################################### Removing bulky code ########################

def value_split(tree, gensym_ix=None):
    # Splits a tree into a "header" and an "output", where the "output" is a symbol.
    if gensym_ix is None:
        gensym_ix = [0]
    if type(tree) is dict:
        ch = 'DICT'
    elif type(tree) is set:
        ch = 'SET'
    else: # Better be a list, else no need to split!.
        t0 = tree[0].value
        ch = 'XYZ' # TODO: better name.
    vname = chr(6220)+ch+str(gensym_ix[0]); gensym_ix[0] = gensym_ix[0]+1
    return py_translate.branch_assign(tree, vname), Symbol(vname)

def extern_bulky(code, gensym_ix=None):
    # Externalizes all the bulky pieces from code.
    # Returns a list of headers (which needs to be DO-wrapped) as well the fixed code (often a symbol).
      # If the list is empty there is no need to change the code.
    if gensym_ix is None:
        gensym_ix = [0]
    if type(code) is dict:
        headers = []; out = {}
        kys = list(code.keys()); kys.sort()
        for ky in kys:
            h1, v1 = extern_bulky(code[ky], gensym_ix)
            headers = headers+h1
            out[ky] = v1
        return headers, out
    elif type(code) is set:
        codev = list(code); codev.sort()
        headers, out = extern_bulky(codev, gensym_ix)
        return headers, set(out)
    elif type(code) is list or type(code) is tuple:
        c0 = code[0]
        if c0 == MOD:
            raise Exception('Cannot blit MOD directly.')
        elif c0.value in {'if','while','for', 'try','catch','raise', 'del'} or ((c0.value=='if') and not simple_if):
            # More of a brute-force approach here.
            head, sym = value_split(code, gensym_ix)
            return [head], sym
        elif c0.value in {'def','class'}: # Use the def'ed symbol.
            sym = code[1]
            return [code], sym
        elif c0.value == '=' or c0==LOCAL or c0==NONLOCAL: # a=b assignment.
            sym = code[1]
            return [code], sym
        elif c0 == DO:
            headers, code_1 = extern_bulky(code[-1], gensym_ix)
            if len(code)>2:
                return code[1:-1]+headers, code_1 # The last statement is the result.
            else: # Single thing in the DO
                return headers, code_1
        elif c0 == MOD:
            raise Exception('Cannot externalize code from a listcomp/dictcomp or similar structure.')
        else: # Function call or op (which can be treated as a fn call in our lispy).
            headers = []
            args = []
            is_op = c0.value in {'+','-','*','/','%','**','//','<','>','<=','>=','==','!='}
            for arg in code[1:]:
                arg = copy.deepcopy(arg)
                is_eq = (not is_op) and _is_asgn(arg) # This can modify arg in place.
                if is_eq: # a=b function arguments.
                    heads1, arg[2] = extern_bulky(arg[2], gensym_ix)
                else:
                    heads1, arg = extern_bulky(arg, gensym_ix)
                headers = headers+heads1
                args.append(arg)
            code1 = code.copy(); code1[1:] = args
            return headers, code1
    else:
        return [], code

def dowrap_uncramp_branches1(tree, gensym_ix=None):
    # Removes top-level "cramps" in tree, wrapping in a do-statement if necessary.
    # Example: (if bulky_a b c) => (do body_of_a (if fixed_a b c))
    #   Note: body_of_a may need further processing, as would nested forms within b, c.
    # Will return the original tree if there is no need at the top level.

    if gensym_ix is None:
        gensym_ix = [0]

    # Special cases:
    if type(tree) is dict or type(tree) is set:
        headers, tree1 = extern_bulky(headers, tree1, gensym_ix)
        if len(headers)>0:
            return ([DO]+headers).append(tree1)
        return tree
    elif type(tree) is not list and type(tree) is not tuple:
        return tree
    elif tree[0] == LISTCOMP: #Dict comps and list comps are special.
        if is_bulky(tree):
            return dowrap_uncramp_branches1(py_translate.expand_listcomp1(tree, gensym_ix), gensym_ix)
        return tree
    elif tree[0] == DICTCOMP:
        if is_bulky(tree):
            return dowrap_uncramp_branches1(py_translate.expand_dictcomp1(tree, gensym_ix), gensym_ix)
        return tree
    elif tree[0] == SPLICE or tree[0] == DO: # No need for externing anything.
        return tree
    elif type(tree[0]) is not Symbol:
        print('Uh ho:', tree[0], type(tree[0]))
        raise Exception('Listy[0] not a symbol')
    elif tree[0].value=='def': # Deal with the args.
        args = copy.deepcopy(tree[2]) # Args should be fairly small most of the time.
        prepends = []
        for a in range(args):
            is_eq = _is_asgn(args[a])
            if is_eq: # a=b function arguments.
                addp, args[a][2] = extern_bulky(prepends, args[a][2], gensym_ix)
            else:
                addp, args[a] = extern_bulky(prepends, args[a], gensym_ix)
            prepends = prepends+addp
        if len(prepends)==0: # No change.
            return tree
        return [DO]+[prepends]+[tree[0], tree[1], args, tree[3]]

    # STANDARD cases: some ixs need to be externed.
    ixs = []
    fn = tree[0].value
    if fn == LIST.value or fn==DICT.value or fn==SET.value or fn==TUPLE.value or fn=='=' or fn==LOCAL.value or fn==NONLOCAL.value or fn==INDEX.value or fn==':' or fn=='import':
        ixs = list(range(1,len(tree)))
    elif fn=='while' or fn == 'if' or fn=='for': # The [1] element can't be bulky.
        ixs = [1]
    elif fn=='class': # No restrictions here.
        ixs = []
    elif fn=='=' or fn==LOCAL.value or fn==NONLOCAL.value:
        ixs = [2]
    else: # Function call. Allows a=b type arguments.
        ixs = list(range(1,len(tree)))

    if len(ixs) == 0:
        return tree # No change.

    tree1 = tree.copy()
    all_headers = []
    for ix in ixs:
        tree1[ix] = copy.deepcopy(tree1[ix])
        #debug_b4 = copy.deepcopy(tree1[ix])
        headix, tree1[ix] = extern_bulky(tree1[ix], gensym_ix)
        #print('Old and new tree ixs:', tree[ix], tree1[ix])
        #debug_aft = tree1[ix]
        #if str(debug_b4) != str(debug_aft):
        #    print('Effect of inplace_extern:', debug_b4, headix, debug_aft)
        if len(headix)>0:
            all_headers = all_headers+headix
    #if fn == 'if':
    #    print('Original if-statement tree:', tree)
    #    print('  Headers:', [DO]+all_headers, ' ixs:', ixs)
    #    print('  New if-statement tree:', tree1)
    if len(all_headers) == 0:
        return tree # Nothing changed!
    else:
        return [DO]+all_headers+[tree1]

def extern_bulky_all(tree, gensym_ix=None, localname=True):
    # Recursive.
    # localname is recommended and will prevent conflicts with externalized code.
    if gensym_ix is None:
        gensym_ix = [0]

    if localname and outer_level_bulky(tree):
        # Prevent the extern_bulky from.
        tree = sunshine.unicode_scope_rename(tree)
        localname = False

    tree1 = dowrap_uncramp_branches1(tree, gensym_ix) # Shallow first!

    if type(tree) is list and tree[0] == Symbol('if'):
        print('Stuff tree if statemnet:', tree, tree1)
    if type(tree1) is dict:
        kys = list(tree1.keys()); kys.sort()
        out = dict(zip(kys, [extern_bulky_all(tree1[k], gensym_ix, localname) for k in kys]))
    elif type(tree1) is set:
        tsort = list(tree1); tsort.sort()
        out = set([extern_bulky_all(branch, gensym_ix, localname) for branch in tsort])
    elif type(tree1) is list or type(tree1) is tuple:
        out = [extern_bulky_all(branch, gensym_ix, localname) for branch in tree1]
    else:
        out = tree1
    return out

##################################Blitting functions ###########################

def core_blit(tree, indent=4):
    # The main blit step that produces a string which can be saved or exec'ed as standard Python.
    # Don't forget to extern_bulky_all
    def add_pass(sp, x): # The AST has no "pass" statements in it, but empty lists are that way.
        if len(x)==0:
            return [sp+'pass']
        return x
    def indent_lines(txt):
        indt = ' '*indent
        pieces = [indt+txti for txti in '\n'.split(txt)]
        return '\n'.join(pieces)

    if tree is None: # Different from the symbol None!
        return ''

    ty = type(tree)

    #leaf_prepend = '' # Under some conditions leaves are indented.
    #if leaf_indent:
    #    leaf_prepend = ' '*(indent*indent_level)
    if ty is dict:
        pairs = []
        for k,v in tree.items():
            pairs.append(core_blit(k, indent)+':'+core_blit(v, indent))
        return '{'+', '.join(pairs)+'}'
    elif ty is set:
        return '{'+[core_blit(br, indent) for br in tree]+'}'
    elif ty is str:
        esc_chars = '\n\t\r\b\f\\"'
        esc_vals = 'ntrbf\\"'
        for i in range(len(esc_chars)):
            tree = tree.replace(esc_chars[i], '\\'+esc_vals[i])
        result = '"'+tree+'"'
    elif ty is not list and type(tree) is not tuple:
        result+str(tree)
    elif len(tree)==0:
        return ''
    else:
        s0 = tree[0] # The symbol.
        sp = ' '*(indent*indent_level)
        sp1 = sp+' '*indent
        simple_if = False
        if s0.value=='if' and not is_bulky(tree):
            simple_if = True
        if simple_if:
            # Special inline if-statement which isn't heavy.
            true_branch = core_blit(tree[2], indent)
            if len(true_branch)==0: # Empty true branch.
                true_branch = 'None'
            false_branch = 'None' #All inline if-statements need an 'else'.
            if len(tree)>3:
                false_branch = core_blit(tree[3], indent)
            return '('+true_branch+' if '+condition+' else '+false_branch+')'
        elif s0.value in {'while', 'for', 'if'}:
            condition = s0.value+' '+core_blit(tree[1], indent, indent_level)+':'
            body = indent_lines(add_pass(core_blit(tree[2], indent)))
            if len(tree)>3:
                elses = indent_lines(add_pass(core_blit(tree[3], indent)))
                return condition+'\n'+body+'\n'+'else:'+elses
            else:
                return condition+'\n'+body
        elif s0.value == 'try': # try-except block.
            body = indent_lines(add_pass(core_blit(tree[1], indent)))
            ex_type = core_blit(tree[2], indent)
            fallback = indent_lines(add_pass(core_blit(tree[3], indent)))
            out = 'try:'+'\n'+body+'\nexcept'+ex_type+':\n'+fallback
            if len(tree)>4:
                final_body = indent_lines(add_pass(core_blit(tree[4], indent)))
                out = out+'\nfinally:\n'+final_body
        elif s0.value == 'raise':
            return 'raise '+core_blit(tree[1], indent)
        elif s0.value in {'*','**'} and len(tree)==2:
            return s0.value+core_blit(tree[1], indent) # Splat ops.
        elif s0.value in {'=','==','<=','>=','-=','+=','*=','/=','<','>','+','-','*','/','**','%','&','&&','|','||','not','in','and','or',':','::'} or s0==LOCAL or s0==NONLOCAL:
            # Binops. Did we catch them all?
            # Note: we expand a += x into a = a+x, so the -= and += not strictly needed.
            out = core_blit(tree[1], indent)+s0.value+core_blit(tree[2], indent)
            if s0.value in {'=','-=','+=','*=','/='}:
                return out # () would cause problems.
            return '('+out+')' # Extra () not always needed but shouldn't cause problems.
        elif s0==LIST:
            return '['+', '.join([core_blit(ti, indent) for ti in tree[1:]])+']'
        elif s0==TUPLE:
            return '('+', '.join([core_blit(ti, indent) for ti in tree[1:]])+')'
        elif s0==LISTCOMP:
            ifs = ''
            pieces = []
            for branch in tree[2:]:
                ifs = ''.join([' if '+core_blit(twig, indent) for twig in branch[3:]])
                pieces.append(' for '+core_blit(branch[1], indent)+' in '+core_blit(branch[2], indent)+ifs)
            return '['+core_blit(tree[1], indent)+''.join(pieces)+']'
        elif s0==DICT:
            ix = 1
            pairs = []
            while ix<len(tree):
                pairs.append(core_blit(tree[ix])+':'+core_blit(tree[ix+1]))
                ix = ix+2
            return '{'+', '.join(pairs)+'}'
        elif s0==DICTCOMP:
            pieces = []
            for branch in tree[3:]:
                ifs = ''.join([' if '+core_blit(twig, indent) for twig in branch[3:]])
                pieces.append(' for '+core_blit(branch[1], indent)+' in '+core_blit(branch[2], indent)+ifs)
            return '{'+core_blit(tree[1], indent)+':'+core_blit(tree[2], indent)+''.join(pieces)+'}'
        elif s0==SET:
            return '{'+', '.join([core_blit(ti, indent) for ti in tree[1:]])+'}'
        elif s0==SPLICE or s0==DO: # Can treat splice like DO.
            return '\n'.join([core_blit(ti, indent) for ti in tree[1:]])
        elif s0==INDEX:
            return core_blit(tree[1])+'['+core_blit(tree[2])+']'
        elif '.-' in s0.value: # Class attributes.
            return core_blit(tree[1])+'.'+s0.value[2:]
        elif '.' in s0.value: # Method calls.
            #foo.bar => .bar foo lisp style.
            args = ', '.join([core_blit(t2, indent) for t2 in tree[2]])
            fnname = s0.value[1:]+'.'+tree[1].value
            return fnname+'('+args+')'
        else: # Function calls.
            args = ', '.join([core_blit(t2, indent) for t2 in tree[1]])
            return tree[0].value+'('+args+')'

################################### The main function ##########################

def blit(code, indent=4, indent_level=0):
    # Blits the code itself.
    code = py_translate.reduce_nesting(code)
    #code = py_translate.unique_local_names(code) # Important for blitting and variable spillage.
    TODO
