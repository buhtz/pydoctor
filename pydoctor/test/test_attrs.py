from typing import Optional, Type

from pydoctor import epydoc2stan, model
from pydoctor.extensions import attrs
from pydoctor.stanutils import flatten_text
from pydoctor.templatewriter import pages
from pydoctor.test import CapSys

from pydoctor.test.test_astbuilder import fromText, AttrsSystem, type2str

import pytest

attrs_systemcls_param = pytest.mark.parametrize(
    'systemcls', (model.System, # system with all extensions enalbed
                  AttrsSystem, # system with attrs extension only
                 ))

def assert_constructor(cls:model.Documentable, sig:str, 
                       shortsig:Optional[str]=None) -> None:
    assert isinstance(cls, model.Class)
    constructor = cls.contents['__init__']
    assert isinstance(constructor, model.Function)
    assert flatten_text(pages.format_signature(constructor)) == sig
    if shortsig:
        assert epydoc2stan.format_constructor_short_text(constructor, forclass=cls) == shortsig


@attrs_systemcls_param
def test_attrs_attrib_type(systemcls: Type[model.System]) -> None:
    """An attr.ib's "type" or "default" argument is used as an alternative
    type annotation.
    """
    mod = fromText('''
    import attr
    from attr import attrib
    @attr.s
    class C:
        a = attr.ib(type=int)
        b = attrib(type=int)
        c = attr.ib(type='C')
        d = attr.ib(default=True)
        e = attr.ib(123)
    ''', modname='test', systemcls=systemcls)
    C = mod.contents['C']

    A = C.contents['a']
    B = C.contents['b']
    _C = C.contents['c']
    D = C.contents['d']
    E = C.contents['e']

    assert isinstance(A, model.Attribute)
    assert isinstance(B, model.Attribute)
    assert isinstance(_C, model.Attribute)
    assert isinstance(D, model.Attribute)
    assert isinstance(E, model.Attribute)

    assert type2str(A.annotation) == 'int'
    assert type2str(B.annotation) == 'int'
    assert type2str(_C.annotation) == 'C'
    assert type2str(D.annotation) == 'bool'
    assert type2str(E.annotation) == 'int'

@attrs_systemcls_param
def test_attrs_attrib_instance(systemcls: Type[model.System]) -> None:
    """An attr.ib attribute is classified as an instance variable."""
    mod = fromText('''
    import attr
    @attr.s
    class C:
        a = attr.ib(type=int)
    ''', modname='test', systemcls=systemcls)
    C = mod.contents['C']
    assert C.contents['a'].kind is model.DocumentableKind.INSTANCE_VARIABLE

@attrs_systemcls_param
def test_attrs_attrib_badargs(systemcls: Type[model.System], capsys: CapSys) -> None:
    """."""
    fromText('''
    import attr
    @attr.s
    class C:
        a = attr.ib(nosuchargument='bad')
    ''', modname='test', systemcls=systemcls)
    captured = capsys.readouterr().out
    assert captured == (
        'test:5: Invalid arguments for attr.ib(): got an unexpected keyword argument "nosuchargument"\n'
        )

@attrs_systemcls_param
def test_attrs_auto_instance(systemcls: Type[model.System]) -> None:
    """Attrs auto-attributes are classified as instance variables."""
    mod = fromText('''
    from typing import ClassVar
    import attr
    @attr.s(auto_attribs=True)
    class C:
        a: int
        b: bool = False
        c: ClassVar[str]  # explicit class variable
        d = 123  # ignored by auto_attribs because no annotation
    ''', modname='test', systemcls=systemcls)
    C = mod.contents['C']
    assert isinstance(C, attrs.AttrsClass)
    assert C.attrs_options['auto_attribs'] == True
    assert C.contents['a'].kind is model.DocumentableKind.INSTANCE_VARIABLE
    assert C.contents['b'].kind is model.DocumentableKind.INSTANCE_VARIABLE
    assert C.contents['c'].kind is model.DocumentableKind.CLASS_VARIABLE
    assert C.contents['d'].kind is model.DocumentableKind.CLASS_VARIABLE

@attrs_systemcls_param
def test_attrs_args(systemcls: Type[model.System], capsys: CapSys) -> None:
    """Non-existing arguments and invalid values to recognized arguments are
    rejected with a warning.
    """
    fromText('''
    import attr

    @attr.s()
    class C0: ...

    @attr.s(repr=False)
    class C1: ...

    @attr.s(auto_attribzzz=True)
    class C2: ...

    @attr.s(auto_attribs=not False)
    class C3: ...

    @attr.s(auto_attribs=1)
    class C4: ...
    ''', modname='test', systemcls=systemcls)
    captured = capsys.readouterr().out
    assert captured == (
        'test:10: Invalid arguments for attr.s(): got an unexpected keyword argument "auto_attribzzz"\n'
        'test:13: Unable to figure out value for "auto_attribs" argument, maybe too complex\n'
        'test:16: Value for "auto_attribs" argument has type "int", expected "bool"\n'
        )

@attrs_systemcls_param
def test_attrs_constructor_method_infer_arg_types(systemcls: Type[model.System], capsys: CapSys) -> None:
    src = '''\
    @attr.s
    class C(object):
        c = attr.ib(default=100)
        x = attr.ib(default=1)
        b = attr.ib(default=23)

    @attr.s(init=False)
    class D(C):
        a = attr.ib(default=42)
        x = attr.ib(default=2)
        d = attr.ib(default=3.14)
    '''
    mod = fromText(src, systemcls=systemcls)
    assert capsys.readouterr().out == ''
    C = mod.contents['C']
    assert isinstance(C, attrs.AttrsClass)
    assert C.attrs_options['init'] is None
    D = mod.contents['D']
    assert isinstance(D, attrs.AttrsClass)
    assert D.attrs_options['init'] is False

    assert_constructor(C, '(self, c: int = 100, x: int = 1, b: int = 23)', 'C(c, x, b)')

# Test case for auto_attribs with defaults
@attrs_systemcls_param
def test_attrs_constructor_auto_attribs(systemcls: Type[model.System]) -> None:
    src = '''\
    import attr
    @attr.s(auto_attribs=True)
    class C:
        a: int
        b: str = "default"
    '''
    mod = fromText(src, systemcls=systemcls)
    assert_constructor(mod.contents['C'], '(self, a: int, b: str = \'default\')')

# Test case for kw_only
@attrs_systemcls_param
def test_attrs_constructor_kw_only(systemcls: Type[model.System]) -> None:
    src = '''\
    import attr
    @attr.s(kw_only=True)
    class C:
        a = attr.ib()
        b: str = attr.ib()
    '''
    mod = fromText(src, systemcls=systemcls)
    C = mod.contents['C']
    assert isinstance(C, attrs.AttrsClass)
    assert C.attrs_options['kw_only'] is True
    assert C.attrs_options['init'] is None
    assert_constructor(C, '(self, *, a, b: str)')

# Test case for default factory
@attrs_systemcls_param
def test_attrs_constructor_factory(systemcls: Type[model.System]) -> None:
    src = '''\
    import attr
    @attr.s(auto_attribs=True)
    class C:
        a: int = attr.ib(factory=list)
        b: str = attr.Factory(str)
        c: list = attr.ib(default=attr.Factory(list))
    '''
    mod = fromText(src, systemcls=systemcls)
    assert_constructor(mod.contents['C'], '(self, a: list = list(), b: str = str(), c: list = list())')
    
@attrs_systemcls_param
def test_attrs_constructor_factory_no_annotations(systemcls: Type[model.System]) -> None:
    src = '''\
    import attr
    @attr.s
    class C:
        a = attr.ib(factory=list)
        b = attr.ib(default=attr.Factory(list))
    '''
    mod = fromText(src, systemcls=systemcls)
    assert_constructor(mod.contents['C'], '(self, a: list = list(), b: list = list())')

# Test case for init=False:
@attrs_systemcls_param
def test_attrs_no_constructor(systemcls: Type[model.System]) -> None:
    src = '''\
    import attr
    @attr.s(init=False)
    class C:
        a: int = attr.ib()
        b: str = attr.ib()
    '''
    mod = fromText(src, systemcls=systemcls)
    C = mod.contents['C']
    assert C.contents.get('__init__') is None

# Test case for single inheritance:
@attrs_systemcls_param
def test_attrs_constructor_single_inheritance(systemcls: Type[model.System]) -> None:
    src = '''\
    import attr
    @attr.s(auto_attribs=True)
    class Base:
        a: int

    @attr.s(auto_attribs=True)
    class Derived(Base):
        b: str
    '''
    mod = fromText(src, systemcls=systemcls)
    assert_constructor(mod.contents['Derived'], '(self, a: int, b: str)', 'Derived(a, b)')

# Test case for multiple inheritance:
@attrs_systemcls_param
def test_attrs_constructor_multiple_inheritance(systemcls: Type[model.System]) -> None:
    src = '''\
    import attr
    @attr.s(auto_attribs=True)
    class Base1:
        a: int

    @attr.s(auto_attribs=True)
    class Base2:
        b: str

    @attr.s(auto_attribs=True)
    class Derived(Base1, Base2):
        c: float
    '''
    mod = fromText(src, systemcls=systemcls)
    assert_constructor(mod.contents['Derived'], '(self, b: str, a: int, c: float)', 'Derived(b, a, c)')

# Test case for inheritance with overridden attributes:
@attrs_systemcls_param
def test_attrs_constructor_single_inheritance_overridden_attribute(systemcls: Type[model.System]) -> None:
    src = '''\
    import attr
    @attr.s(auto_attribs=True)
    class Base:
        a: int
        b: str = "default"

    @attr.s(auto_attribs=True)
    class Derived(Base):
        b: str = "overridden"
        c: float = 3.14
    '''
    mod = fromText(src, systemcls=systemcls)
    assert_constructor(mod.contents['Derived'], '(self, a: int, b: str = \'overridden\', c: float = 3.14)', 'Derived(a, b, c)')

@attrs_systemcls_param
def test_attrs_constructor_single_inheritance_traverse_subclasses(systemcls: Type[model.System]) -> None:
    src = '''\
    import attr
    @attr.s(auto_attribs=True)
    class FieldDesc:
        name: Optional[str] = None
        type: Optional[Tag] = None
        body: Optional[Tag] = None

    @attr.s(auto_attribs=True)
    class _SignatureDesc(FieldDesc):
        type_origin: Optional[object] = None

    @attr.s(auto_attribs=True)
    class ReturnDesc(_SignatureDesc):...
    '''

    mod = fromText(src, systemcls=systemcls)
    assert_constructor(mod.contents['ReturnDesc'], 
                       '(self, name: Optional[str] = None, type: Optional[Tag] = None, body: Optional[Tag] = None, type_origin: Optional[object] = None)',
                       'ReturnDesc(name, type, body, type_origin)')

# Test case with attr.ib(init=False):
@attrs_systemcls_param
def test_attrs_constructor_attribute_init_False(systemcls: Type[model.System]) -> None:
    src = '''\
    import attr
    @attr.s(auto_attribs=True)
    class MyClass:
        a: int
        b: str = attr.ib(init=False)
    '''
    mod = fromText(src, systemcls=systemcls)
    assert_constructor(mod.contents['MyClass'], '(self, a: int)')

# Test case with attr.ib(kw_only=True):
@attrs_systemcls_param
def test_attrs_constructor_attribute_kw_only_reorder(systemcls: Type[model.System], capsys:CapSys) -> None:
    src = '''\
    import attr
    @attr.s(auto_attribs=True)
    class MyClass:
        a: int
        b: str = attr.ib(kw_only=True)
        c: float
    '''
    mod = fromText(src, systemcls=systemcls)
    assert not capsys.readouterr().out
    assert_constructor(mod.contents['MyClass'], '(self, a: int, c: float, *, b: str)')

@attrs_systemcls_param
def test_converter_init_annotation(systemcls:Type[model.System]) -> None:
    src = '''\
    import attr

    class Stuff:
        ...

    def convert_to_upper(value: object) -> str:
        return str(value).upper()

    @attr.s
    class MyClass:
        name: str = attr.ib(converter=convert_to_upper)
        st:Stuff = attr.ib(converter=Stuff)
        age:int = attr.ib(converter=int)
    '''

    mod = fromText(src, systemcls=systemcls)
    assert_constructor(mod.contents['MyClass'], '(self, name: object, st: Stuff, age: object)')

@attrs_systemcls_param
def test_auto_detect_init(systemcls:Type[model.System]) -> None:
    src = '''\
    import attr

    @attr.s(auto_detect=True, auto_attribs=True)
    class MyClass:
        a: int
        b: str

        def __init__(self):
            self.a = 1
            self.b = 0

        '''
    
    mod = fromText(src, systemcls=systemcls)
    assert_constructor(mod.contents['MyClass'], '(self)')
    
@attrs_systemcls_param
def test_auto_detect_is_False_init_overriden(systemcls:Type[model.System]) -> None:
    src = '''\
    import attr

    @attr.s(auto_detect=False, auto_attribs=True)
    class MyClass:
        a: int
        b: str

        def __init__(self):
            self.a = 1
            self.b = 0

        '''
    
    mod = fromText(src, systemcls=systemcls)
    assert_constructor(mod.contents['MyClass'], '(self, a: int, b: str)')

@attrs_systemcls_param
def test_auto_detect_is_True_init_is_True(systemcls:Type[model.System]) -> None:
    # Passing ``True`` or ``False`` to *init*, *repr*, *eq*, *order*,
    #     *cmp*, or *hash* overrides whatever *auto_detect* would determine.
    
    src = '''\
    import attr

    @attr.s(auto_detect=True, auto_attribs=True, init=True)
    class MyClass:
        a: int
        b: str

        def __init__(self):
            self.a = 1
            self.b = 0

        '''
    
    mod = fromText(src, systemcls=systemcls)
    assert_constructor(mod.contents['MyClass'], '(self, a: int, b: str)')

@attrs_systemcls_param
def test_field_keyword_only_inherited_parameters(systemcls) -> None:
    src = '''\
    import attr
    @attr.s
    class A:
        a = attr.ib(default=0)
    @attr.s
    class B(A):
        b = attr.ib(kw_only=True)
        '''
    mod = fromText(src, systemcls=systemcls)
    assert_constructor(mod.contents['B'], '(self, a: int = 0, *, b)')

@attrs_systemcls_param
def test_class_keyword_only_inherited_parameters(systemcls) -> None:
    # see https://github.com/python-attrs/attrs/commit/123df6704176d1981cf0d8f15a5021f4e2ce01ed
    src = '''\
    import attr
    @attr.s
    class A:
        a = attr.ib(default=0)
    @attr.s(kw_only=True)
    class B(A):
        b = attr.ib()
        '''
    mod = fromText(src, systemcls=systemcls)
    assert_constructor(mod.contents['A'], '(self, a: int = 0)')
    assert_constructor(mod.contents['B'], '(self, *, a: int = 0, b)', 'B(a, b)')

    src = '''\
    import attr
    @attr.s(auto_attribs=True)
    class A:
        a:int
    @attr.s(auto_attribs=True, kw_only=True)
    class B(A):
        b:int
    '''
    mod = fromText(src, systemcls=systemcls)
    assert_constructor(mod.contents['A'], '(self, a: int)')
    assert_constructor(mod.contents['B'], '(self, *, a: int, b: int)', 'B(a, b)')