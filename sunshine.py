# Prevents vars from shadowding eachother.
#  (for now it only prevents shadowing vars of outside scope).
# Trailing unicode characters determine where the code is.
# Central to this is a lineage system: Trailing unicode (greek, etc)
    # is used to track where we are in a given scope.

from . import symbol
symbol.sym_splat(__name__)

nice_unicodes = []
def _init_nice_unicodes():
    print("We like our unicode chars good_looking and Python-approved.")
    x = nice_unicodes
    for i in range(0x3b1,0x3c9+1): #Greek lowercase.
        x.append(i)
    for i in range(0x531, 0x556+1): #Armenian.
        x.append(i)
    for i in range(0x561, 0x587+1): #Armenian take2
        x.append(i)
    for i in range(0x676, 0x6d3+1): #Arabic.
        x.append(i)
    for i in range(0x5d0, 0x5ea+1): #Hebrew.
        x.append(i)
    for i in range(0x904, 0x939+1): #Devanagari
        x.append(i)
    for i in range(0x144c, 0x167d+1): #Canada native (constructed)
        x.append(i)

def outer_lineage(tree):
    # Guesses the outer lineage from trailing unicode of vars.
    # This means that a context_walk on an isolated piece of code will still work.
    TODO

def context_walk(tree, f, context=None):
    # Applies f with a context which stores information about variables.
    # Calls f(tree, context).
    # target_path will allow us to only apply f to target_path, but still compute the context.

    if len(nice_unicodes)==0:
        _init_nice_unicodes()
    if context is None:
        context = {}
        context['lineage'] = outer_lineage(tree) # Unicode string for the local blocks.
        context['localss'] = [set()] # Local vars defined at each level.
        context['local_ix'] = 0 # Used mainly to inform lineage.
        context['path'] = [] # All descendent paths.

    def _recurs(branches, ixs, context1):
        # Recursive. Still allows in-place changes to context1.
        out = []
        context1['path'].append(-1)
        for i in range(len(ixs)):
            context1['path'][-1] = [i]
            out.append(context_walk(branches[i], f, context1))
        context1['path'] = context1['path'][0:-1]
        return out
    tree = f(tree, context)

    if type(tree) is list or type(tree) is tuple:
        t0 = py_translate.fname(tree)
        c = chr(nice_unicodes[context['local_ix']])
        ixs = range(len(tree))

        if t0=='=' and (type(tree[1]) is Symbol): # a[1] = b will fail the second criterion and does not assign any vars.
            tail = _recurs(tree[2:], ixs[2:], context) # We haven't defined the var yet.
            context['localss'][-1].add(tree[1].value)
            head = _recurs(tree[0:2], ixs[0:2], context) # For the x in x=1 we have defined the var x.
            return head + tail
        elif t0=='class' or t0=='def' or t0==LISTCOMP.value or t0==DICTCOMP.value or t0==LOCAL.value: # SCOPE IN.
            # Locals are of the form [L=, x, 1, <body>].
            # The <body> references the var created much like what can happen in def.
            kx = 1 # Where the var itself is.
            newvar_outer = True # Is the var defined by this block outside the scope created by this block?
            context1 = context.copy()
            if t0==LISTCOMP.value or t0==DICTCOMP.value:
                kx = 2
                context1['localss'] = context['localss'].copy()
                newvar_outer = False
            context1['lineage'] = context1['lineage']+c
            context1['local_ix'] = 0
            if newvar_outer:
                context1['localss'][-1].add(tree[kx].value)
            context1['localss'].append(set()) # Add a level.
            if not newvar_outer:
                context1['localss'][-1].add(tree[kx].value)
            out = _recurs(tree, ixs, context1)
            context['local_ix'] = context['local_ix']+1 # Updater after recursive.
            return out
        else: # Nothing special.
            return _recurs(tree, ixs, context)
    elif type(tree) is dict:
        return dict(zip(kys, _recurs(tree, ixs, context)))
    elif type(tree) is set:
        tree1 = list(tree); tree1.sort() # sort makes deterministic.
        return set(_recurs(tree, ixs, context))
    else:
        return tree

def unicode_scope_rename(tree, clear_old_unicode=True):

    def _rename_txt(txt, lineage):
        # Only rename vars that have been declared.
        if clear_old_unicode: 
            txt = txt.encode("ascii", "ignore").decode()
        return txt+lineage

    def f(branch, context): 
        if type(branch) is Symbol:
            #print('Branch:', context['localss'], branch.value)
            for i in range(1, len(context['localss'])):
                if branch.value in context['localss'][i]:
                    return Symbol(_rename_txt(branch.value, context['lineage'][0:i]))
            #print('Stuff:', context, branch)
        return branch

    return context_walk(tree, f, context=None)

def inline_code(tree, path, new_branch):
    
    TODO