"""
These tests test the cases that the old fast parser tested with the normal
parser.

The old fast parser doesn't exist anymore and was replaced with a diff parser.
However the tests might still be relevant for the parser.
"""

from textwrap import dedent

import jedi
from jedi._compatibility import u
from jedi.parser.python import parse


def test_carriage_return_splitting():
    source = u(dedent('''



        "string"

        class Foo():
            pass
        '''))
    source = source.replace('\n', '\r\n')
    module = parse(source)
    assert [n.value for lst in module.get_used_names().values() for n in lst] == ['Foo']


def test_class_in_docstr():
    """
    Regression test for a problem with classes in docstrings.
    """
    a = '"\nclasses\n"'
    jedi.Script(a, 1, 0)._get_module()

    b = a + '\nimport os'
    assert jedi.Script(b, 4, 8).goto_assignments()


def check_p(src, number_parsers_used, number_of_splits=None, number_of_misses=0):
    if number_of_splits is None:
        number_of_splits = number_parsers_used

    module_node = parse(src)

    assert src == module_node.get_code()
    return module_node


def test_if():
    src = dedent('''\
    def func():
        x = 3
        if x:
            def y():
                return x
        return y()

    func()
    ''')

    # Two parsers needed, one for pass and one for the function.
    check_p(src, 2)
    assert [d.name for d in jedi.Script(src, 8, 6).goto_definitions()] == ['int']


def test_for():
    src = dedent("""\
    for a in [1,2]:
        a

    for a1 in 1,"":
        a1
    """)
    check_p(src, 1)


def test_class_with_class_var():
    src = dedent("""\
    class SuperClass:
        class_super = 3
        def __init__(self):
            self.foo = 4
    pass
    """)
    check_p(src, 3)


def test_func_with_if():
    src = dedent("""\
    def recursion(a):
        if foo:
            return recursion(a)
        else:
            if bar:
                return inexistent
            else:
                return a
    """)
    check_p(src, 1)


def test_decorator():
    src = dedent("""\
    class Decorator():
        @memoize
        def dec(self, a):
            return a
    """)
    check_p(src, 2)


def test_nested_funcs():
    src = dedent("""\
    def memoize(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    """)
    check_p(src, 3)


def test_class_and_if():
    src = dedent("""\
    class V:
        def __init__(self):
            pass

        if 1:
            c = 3

    def a_func():
        return 1

    # COMMENT
    a_func()""")
    check_p(src, 5, 5)
    assert [d.name for d in jedi.Script(src).goto_definitions()] == ['int']


def test_multi_line_params():
    src = dedent("""\
    def x(a,
          b):
        pass

    foo = 1
    """)
    check_p(src, 2)


def test_class_func_if():
    src = dedent("""\
    class Class:
        def func(self):
            if 1:
                a
            else:
                b

    pass
    """)
    check_p(src, 3)


def test_multi_line_for():
    src = dedent("""\
    for x in [1,
              2]:
        pass

    pass
    """)
    check_p(src, 1)


def test_wrong_indentation():
    src = dedent("""\
    def func():
        a
         b
        a
    """)
    #check_p(src, 1)

    src = dedent("""\
    def complex():
        def nested():
            a
             b
            a

        def other():
            pass
    """)
    check_p(src, 3)


def test_strange_parentheses():
    src = dedent("""
    class X():
        a = (1
    if 1 else 2)
        def x():
            pass
    """)
    check_p(src, 2)


def test_fake_parentheses():
    """
    The fast parser splitting counts parentheses, but not as correct tokens.
    Therefore parentheses in string tokens are included as well. This needs to
    be accounted for.
    """
    src = dedent(r"""
    def x():
        a = (')'
    if 1 else 2)
        def y():
            pass
        def z():
            pass
    """)
    check_p(src, 3, 2, 1)


def test_additional_indent():
    source = dedent('''\
    int(
      def x():
          pass
    ''')

    check_p(source, 2)


def test_incomplete_function():
    source = '''return ImportErr'''

    script = jedi.Script(dedent(source), 1, 3)
    assert script.completions()


def test_string_literals():
    """Simplified case of jedi-vim#377."""
    source = dedent("""
    x = ur'''

    def foo():
        pass
    """)

    script = jedi.Script(dedent(source))
    assert script._get_module().tree_node.end_pos == (6, 0)
    assert script.completions()


def test_decorator_string_issue():
    """
    Test case from #589
    """
    source = dedent('''\
    """
      @"""
    def bla():
      pass

    bla.''')

    s = jedi.Script(source)
    assert s.completions()
    assert s._get_module().tree_node.get_code() == source


def test_round_trip():
    code = dedent('''
    def x():
        """hahaha"""
    func''')

    assert parse(code).get_code() == code


def test_parentheses_in_string():
    code = dedent('''
    def x():
        '('

    import abc

    abc.''')
    check_p(code, 2, 1, 1)
