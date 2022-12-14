from textwrap import dedent
import ast
from typing import Optional

import pytest

from pydoctor import symbols

def getScope(text:str, modname:str='test') -> symbols.Scope:
    mod = ast.parse(dedent(text))
    return symbols.buildSymbols(mod, name=modname)

def test_symbols_module_level() -> None:
    src = '''
    from pydoctor.model import Class, Function as F
    import numpy as np, re, platform
    
    try:
        from foobar import FooBar
    except ModuleNotFoundError:
        class FooBar:
            """Stub for Foobar"""

    if platform.system() == 'Linux':
        def greet_os():
            print('Hello Tux!')
    elif platform.system() == 'Darwin':
        def greet_os():
            print('Hello Mac!')
    else:
        def greet_os():
            print('Hello Win!')

    '''

    scope = getScope(src)
    assert all(k in scope.symbols for k in ('Class', 'F', 'np', 're', 'FooBar', 'greet_os'))

    foostmt1, foostmt2 = scope.symbols['FooBar'].statements
    assert not foostmt1.constraints
    constraint, = foostmt2.constraints
    assert isinstance(constraint, symbols.ExceptHandlerConstraint)
    assert constraint.types == ['ModuleNotFoundError']

    greetstmt1, greetstmt2, greetstmt3 = scope.symbols['greet_os'].statements

    constraint1, = greetstmt1.constraints
    constraint2a, constraint2b, = greetstmt2.constraints
    constraint3a, constraint3b, = greetstmt3.constraints
    
    assert isinstance(constraint1, symbols.IfConstraint)
    assert isinstance(constraint2a, symbols.ElseConstraint)
    assert isinstance(constraint2b, symbols.IfConstraint)
    assert isinstance(constraint3a, symbols.ElseConstraint)
    assert isinstance(constraint3b, symbols.ElseConstraint)

def test_symbols_method() -> None:
    src = '''
    class C:
        def f(self, a, b:int=3, *ag, **kw):
            self.a, self.b = a,b
            self.d = dict(**kw)
    '''

    mod_scope = getScope(src)
    class_scope = mod_scope['C'][0]
    assert isinstance(class_scope, symbols.Scope)
    func_scope = class_scope['f'][0]
    assert isinstance(func_scope, symbols.Scope)

    assert isinstance(func_scope['self'][0], symbols.Arguments)
    assert isinstance(func_scope['a'][0], symbols.Arguments)
    assert isinstance(func_scope['b'][0], symbols.Arguments)
    assert isinstance(func_scope['ag'][0], symbols.Arguments)
    assert isinstance(func_scope['kw'][0], symbols.Arguments)

    assert func_scope['self.d']
    assert func_scope['self.a']
    assert func_scope['self.b']

def test_del_statement() -> None:
    src = '''
    f = Factory()
    rand = f.rand
    del f    
    '''

    mod_scope = getScope(src)
    stmts = mod_scope['f']
    assert len(stmts) == 2
    _, delstmt = stmts
    assert isinstance(delstmt.node, ast.Delete)

def test_global_nonlocal() -> None:
    src = '''
    v = Tue
    def f(a:int, b:int, c:bool) -> int:
        global v 
        if c:
            v = c
        d = False
        def g(a,b) -> int:
            nonlocal d
            d = a*b
            return 
        g(a,b)
        return d
    '''

def test_localNameToFullName() -> None:

    mod = getScope('''
    class session:
        from twisted.conch.interfaces import ISession
        sc = ISession
    ''', modname='test')

    assert mod['session'][0].fullName() == 'test.session' #type:ignore[union-attr]

    def lookup(name: str) -> Optional[str]:
        return symbols.localNameToFullName(mod['session'][0], mod['session'][0], name=name)

    # Local names are returned with their full name.
    assert lookup('session') == 'test.session'

    # Unknown names throws an exceptions
    with pytest.raises(LookupError):
        lookup('nosuchname')
    
    # Dotted names are not supported
    with pytest.raises(LookupError):
        lookup('session.nosuchname')
    
    with pytest.raises(LookupError):
        lookup('session.ISession')
    
    # Aliases are not supported
    assert lookup('sc') == 'test.session.sc'
    
    # Imports are supported, tho
    assert lookup('ISession') == 'twisted.conch.interfaces.ISession'
    