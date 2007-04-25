class C:
    """Class docstring."""
    class S:
        pass
    def f(self):
        """Method docstring."""
    def h(self):
        """Method docstring."""
    @classmethod
    def cls_method(cls):
        pass
    @staticmethod
    def static_method():
        pass


class D(C):
    """Subclass docstring."""
    class T:
        pass
    def f(self):
        # no docstring, should be inherited from superclass
        pass
    def g(self):
        pass
    @classmethod
    def cls_method2(cls):
        pass
    @staticmethod
    def static_method2():
        pass
