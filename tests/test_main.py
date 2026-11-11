import ast
import inspect
import textwrap

from pathlib import Path
from shutil import rmtree

import wrapt

import main
from main import FLAVORS
from main import Example
from main import mark_badges
from main import parse_docstring
from main import parse_function
from main import get_content
from main import split_letters
from main import generate_css


def test_split_letters():
    assert split_letters('a bc') == '<i>a</i><i> </i><i>b</i><i>c</i>'


def test_split_letters_escapes_html():
    assert split_letters('<a') == '<i>&lt;</i><i>a</i>'


def test_generate_css_creates_output_folder():
    here = Path(__file__).parent
    fixture_input = here / 'fixtures' / 'css' / 'sass'
    fixture_output = here / 'fixtures' / 'css' / 'css'
    if fixture_output.exists():
        rmtree(str(fixture_output))
    assert not fixture_output.exists()
    generate_css(fixture_input, fixture_output)
    assert fixture_output.exists()


def test_generate_css_output_folder_exists():
    """
    If the output folder already exists, the code should use it.
    """
    here = Path(__file__).parent
    fixture_input = here / 'fixtures' / 'css' / 'sass'
    fixture_output = here / 'fixtures' / 'css' / 'css'
    if not fixture_output.exists():
        fixture_output.mkdir(parents=True)
    assert fixture_output.exists()
    generate_css(fixture_input, fixture_output)
    assert fixture_output.exists()


def test_generate_css(tmpdir):
    here = Path(__file__).parent
    fixture_input = here / 'fixtures' / 'css' / 'sass'
    fixture_output = Path(str(tmpdir))
    mapping = generate_css(fixture_input, fixture_output)
    assert (fixture_output / 'style.cf83e135.css').exists()
    assert mapping == {'style.scss': 'style.cf83e135.css'}


def test_parse_docstring_without_docstring():
    assert parse_docstring('') == (None, None)
    assert parse_docstring('  ') == (None, None)
    assert parse_docstring(None) == (None, None)


def test_parse_docstring_with_title_and_description():
    assert parse_docstring('# title\n\ndescription') == ('title', 'description')


def test_parse_docstring_with_title_only():
    assert parse_docstring('# title') == ('title', None)
    assert parse_docstring('# title\n\n') == ('title', None)


def test_parse_docstring_without_title():
    """
    If a docstring contains multiple lines but the first one doesn't start
    with a #, the whole docstring is considered the description.
    """
    assert parse_docstring('not the title\nnot the title') == (None, 'not the title\nnot the title')
    assert parse_docstring('not the title') == (None, 'not the title')


def since(*version):
    def decorator(func):
        return func
    return decorator


def dummy_long():
    """
    # Title

    Blah
    """

    x = {'a': 1}

    percent_result = "%(a)s" % x
    format_result = "{x[a]}".format(x=x)
    fstring_result = f"{x['a']}"

    assert percent_result == format_result == fstring_result == "1"  # output


def test_parse_function_complete():
    example = parse_function(*func_to_ast(dummy_long))

    assert example.name == 'dummy_long'
    assert example.title == "Title"
    assert example.details == "Blah"
    assert example.setup == "x = {'a': 1}"
    assert example.variants == {
        'percent': '"%(a)s" % x',
        'format': '"{x[a]}".format(x=x)',
        'fstring': 'f"{x[\'a\']}"',
    }
    assert list(example.variants) == ['percent', 'format', 'fstring']
    assert example.output == "1"
    assert example.since is None


def dummy_minimal():
    format_result = "{}".format(1)

    assert format_result == "1"  # output


def test_parse_function_minimal():
    example = parse_function(*func_to_ast(dummy_minimal))

    assert example.name == 'dummy_minimal'
    assert example.title is None
    assert example.details is None
    assert example.setup == ""
    assert example.variants == {'format': '"{}".format(1)'}
    assert example.output == "1"


def dummy_empty():
    pass


def test_parse_function_empty():
    example = parse_function(*func_to_ast(dummy_empty))

    assert example.name == 'dummy_empty'
    assert example.title is None
    assert example.details is None
    assert example.setup == "pass"
    assert example.variants == {}
    assert example.output == ""


def dummy_variant_order():
    a = 1

    fstring_result = f'{a}'
    percent_result = '%s' % a

    assert fstring_result == percent_result == '1'


def test_parse_function_orders_variants_like_flavors():
    example = parse_function(*func_to_ast(dummy_variant_order))
    assert list(example.variants) == ['percent', 'fstring']


@since(3, 8)
def dummy_debug():
    user = 'eric'  # a user

    # the f-string
    fstring_result = f'{user = }'

    assert fstring_result == "user = 'eric'"  # output


def test_parse_function_keeps_source_verbatim():
    """
    ``ast.unparse`` would turn ``f'{user = }'`` into ``f'user = {user!r}'``,
    so the code has to be taken from the source as written.
    """
    example = parse_function(*func_to_ast(dummy_debug))

    assert example.setup == "user = 'eric'  # a user"
    assert example.variants == {'fstring': "f'{user = }'"}
    assert example.output == "user = 'eric'"
    assert example.since == (3, 8)
    assert example.since_label == "Python 3.8+"


def dummy_multiline():
    a = 1
    b = 2

    fstring_result = f'{
        a + b  # sum
    }'

    assert fstring_result == '3'  # output


def test_parse_function_multiline():
    example = parse_function(*func_to_ast(dummy_multiline))

    assert example.setup == "a = 1\nb = 2"
    assert example.variants == {
        'fstring': "f'{\n    a + b  # sum\n}'",
    }


@wrapt.decorator
def dummy_decorator(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)


@dummy_decorator
def dummy_decorated():
    pass


def test_parse_decorated():
    example = parse_function(*func_to_ast(dummy_decorated))
    assert example.name == 'dummy_decorated'
    assert example.setup == 'pass'


def test_mark_badges():
    examples = mark_badges([
        Example('a', title='A', since=(3, 8)),
        Example('b', since=(3, 8)),
        Example('c', since=(3, 12)),
        Example('d', title='D'),
        Example('e', since=(3, 11)),
        Example('f', title='F', since=(3, 11)),
    ])
    assert [e.show_badge for e in examples] == [True, False, True, False, True, True]


def test_get_content_for_cls(tmpdir):
    testfile = tmpdir.join('test_content.py')
    testfile.write('''
class TestSomethingElse():
    """
    # Title

    Description
    """
    def test_se(self):
        pass

    ''')
    result = list(get_content(filename=Path(str(testfile))))
    assert len(result) == 1
    section = result[0]
    assert section.title == "Title"
    assert section.details == "Description"
    assert section.name == "SomethingElse"
    assert len(section.examples) == 1
    assert section.examples[0].name == "SomethingElse__se"


def test_get_content(tmpdir):
    testfile = tmpdir.join('test_content.py')
    testfile.write('''
def test_something():
    format_result = '{}'.format('hello')
    assert format_result == 'hello'

class TestSomethingElse():
    def test_se(self):
        pass

def unknown():
    pass
    ''')

    result = list(get_content(filename=Path(str(testfile))))
    assert len(result) == 2


def test_render_html(monkeypatch):
    monkeypatch.setattr(main, 'generate_css', lambda *args: {'style.scss': 'style.css'})
    examples = mark_badges([
        Example('both', title='Both', setup='x = 1',
                variants={'percent': "'%s' % x", 'fstring': "f'{x}'"},
                output='1', since=(3, 11)),
        Example('template', title='Template',
                variants={'tstring': "t'{x}'"}, output='<x>'),
    ])
    html = main.render_html(examples)

    assert 'data-flavor-toggle="percent"' in html
    assert 'data-flavor-toggle="tstring"' not in html
    assert '<span class="badge">Python 3.11+</span>' in html
    # Missing selectable variants get a placeholder ...
    assert 'Not possible with .format()' in html
    # ... but only for examples that have at least one selectable variant.
    assert 'Not possible with f-strings' not in html
    assert html.count('class="variant not-possible"') == 1
    assert '<i>&lt;</i><i>x</i><i>&gt;</i>' in html


def test_every_result_is_asserted():
    """
    Every code snippet shown on the page must be checked by an assert in its
    example, otherwise its output isn't verified.
    """
    content = Path(__file__).parent / 'test_content.py'
    module = ast.parse(content.read_text(encoding='utf-8'))
    result_names = {flavor.variable for flavor in FLAVORS}
    checked = 0
    for node in module.body:
        if not (isinstance(node, ast.FunctionDef) and node.name.startswith('test_')):
            continue
        assigned = {
            target.id
            for n in node.body if isinstance(n, ast.Assign)
            for target in n.targets
            if isinstance(target, ast.Name) and target.id in result_names
        }
        asserted = {
            name.id
            for n in node.body if isinstance(n, ast.Assert)
            for name in ast.walk(n.test) if isinstance(name, ast.Name)
        }
        assert assigned, '{} shows no code'.format(node.name)
        assert assigned <= asserted, '{} doesn\'t assert {}'.format(
            node.name, ', '.join(sorted(assigned - asserted)))
        checked += 1
    assert checked > 50


def func_to_ast(func):
    source = textwrap.dedent(inspect.getsource(func))
    return ast.parse(source).body[0], source
