# Translate between various tree modes.
# Translations are bidirectional and largly independent.

import copy
from . import symbol
symbol.sym_splat(__name__)


########################## Data structure complexity ###########################

def make_pure_list(tree):
    # Could a pure list be easier to work with?
    if type(tree) is dict:
        kys = list(tree.keys()); kys.sort()
        out = [DICT]
        for ky in kys:
            out.append(make_pure_list(ky))
            out.append(make_pure_list(tree[ky]))
        return out
    elif type(tree) is set:
        tl = list(tree); tl.sort()
        return [SET]+[make_pure_list(t) for t in tl]
    elif type(tree) is list:
        [make_pure_list(t) for t in tl]
    else:
        return tree

def make_mixed_type(tree):
    # Undoes the effect of make_pure_list.
    TODO

def detailed_assign(tree):
    # Replaces [= [INDEX x 2] 3] with [ASET x 2 3].
    TODO

def undetailed_assign(tree):
    # Inverts detailed_assign
    TODO


