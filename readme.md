# Python metaprogramming tools.

There are two general tools here. This project is very much a WIP.

Main tools:

1. Read Python code into lisp-like abstract syntax trees, *allow full lisp-like manipulation of them*, and blit back as a string.

2. "Hot-patch" python code to change it's behavior at runtime. This includes a logging-tool which can inspect variables.

3. (planned) Allow Clojure-like nested quotes-unquotes, with some modifications to account for Python's non parenthetical syntax.
