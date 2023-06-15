# The symbol class. Like a string but it prints without quotes for ease-of-readibility.
import sys
class Symbol:
    # Ths Symbol class reproduces Clojure-like print behavior.
    # The alternative is Strings instead of Symbols. More clumsy to print and needs to wrap string literals.

    def __init__(self, txt):
        self.value = str(txt)

    #https://stackoverflow.com/questions/35121902/python-how-to-recursively-apply-str-in-print
    def __repr__(self):
        return self.value

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        if type(other) is not Symbol:
            return False
        return self.value == other.value

    # Special forms mean that inner levels arent evaled normally.
    specials = {'if', 'def', 'lambda', 'import'}
    def is_special(self):
        return self.value in specials

# Symbols that aren't valid Python but indicate what the code is:
LIST = Symbol('LIST:') # List literals. The first element of the list isn't called as a "function" or operator.
TUPLE = Symbol('TUPL:') # Tuple literals.
LISTCOMP = Symbol('[...]:') # List comprehensions.
DICT = Symbol('DICT:') # Used when we replace dict literals in the tree with lists.
DICTCOMP = Symbol('{...}:') # Dict comprehensions.
SET = Symbol('SET:') # Used when we replace set literals in the tree with lists.
SPLICE = Symbol('<*>') # Gets spliced into parent form. The ~ is from Clojure. Splice symbols inside an array are deleted.
LOCAL = Symbol('L=') # Indicates a local asignment of the form [L=, x, 1, <body>]. A 1-var lispy let.
NONLOCAL = Symbol('G=') # Global =. Prevents sunshine from de-shadowing. Used when mixed-scope vars can be created.
DO = Symbol('DO:') # Evals to the last element of the list, earlier elements can define vars or have other side effects.
INDEX = Symbol('[]:') # foo[10] array index.
MOD = Symbol('>->') # Used when a higher level modifies how this code gets blitted. For now this means list/dict comps.
# TODO: possible future features.
#INDENT = Symbol('TAB->:') # Embeding an ast into vanilla Python code, indent avode parent level.
#DEDENT = Symbol('UNTAB<-:') # Embeding an ast into vanilla Python code, dedent below parent level.

def sym_splat(modulename):
    # Use like this: sym_splat(_name__)
    # Splats LIST, TUPLE, etc as well as Symbol() into the module's attributes much like C++ #include.
    var_dict = sys.modules[__name__].__dict__
    module = sys.modules[modulename]
    for k in var_dict.keys():
        if '__' not in k:
            setattr(module, k, var_dict[k])
