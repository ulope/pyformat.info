import ast
import inspect
import sys
import textwrap

from pathlib import Path
from shutil import rmtree

import pytest
import wrapt
from click.testing import CliRunner

import main
from main import FLAVORS
from main import ContentError
from main import Example
from main import content_modules
from main import mark_badges
from main import required_python
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


# Kept in a string because multi-line f-string expressions are a syntax
# error before Python 3.12, and this module has to parse on older versions.
MULTILINE_SOURCE = """\
def dummy_multiline():
    a = 1
    b = 2

    fstring_result = f'{
        a + b  # sum
    }'

    assert fstring_result == '3'  # output
"""


@pytest.mark.skipif(sys.version_info < (3, 12),
                    reason="Multi-line f-string expressions need Python 3.12+")
def test_parse_function_multiline():
    example = parse_function(ast.parse(MULTILINE_SOURCE).body[0], MULTILINE_SOURCE)

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


ROOT = Path(__file__).parent.parent


def collectable_content_modules():
    """The content modules that this Python version can parse and test."""
    return [
        path for path, version in content_modules(ROOT / 'tests')
        if not version or sys.version_info >= version
    ]


def test_every_result_is_asserted():
    """
    Every code snippet shown on the page must be checked by an assert in its
    example, otherwise its output isn't verified.
    """
    result_names = {flavor.variable for flavor in FLAVORS}
    checked = 0
    for content in collectable_content_modules():
        module = ast.parse(content.read_text(encoding='utf-8'))
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
    assert checked > 0


def test_content_module_names_match_their_syntax():
    """
    A content module must parse exactly on the Python versions its name
    promises: ``test_content.py`` everywhere, ``test_content_py3NN.py`` from
    3.NN on. Otherwise examples would either break older versions or not be
    tested on versions that could run them.
    """
    for path, version in content_modules(ROOT / 'tests'):
        try:
            ast.parse(path.read_text(encoding='utf-8'))
            parses = True
        except SyntaxError:
            parses = False
        expected = not version or sys.version_info >= version
        assert parses == expected, (
            '{} {} on Python {}.{}, rename it or move its examples'.format(
                path.name, 'parses' if parses else "doesn't parse",
                *sys.version_info[:2]))


def test_content_modules(tmp_path):
    for name in ('test_content.py', 'test_content_py314.py',
                 'test_content_py312.py', 'test_content_pyxyz.py', 'other.py'):
        (tmp_path / name).write_text('')

    assert content_modules(tmp_path) == [
        (tmp_path / 'test_content.py', None),
        (tmp_path / 'test_content_py312.py', (3, 12)),
        (tmp_path / 'test_content_py314.py', (3, 14)),
    ]
    assert required_python(tmp_path) == (3, 14)


def test_required_python_without_versioned_modules(tmp_path):
    (tmp_path / 'test_content.py').write_text('')
    assert required_python(tmp_path) is None


def write_content(folder, toc, **modules):
    for name, source in modules.items():
        (folder / '{}.py'.format(name)).write_text(textwrap.dedent(source))
    toc_path = folder / 'toc.toml'
    toc_path.write_text('sections = {}\n'.format(
        '[{}]'.format(', '.join('"{}"'.format(name) for name in toc))))
    return toc_path


SECTION_A = """
def test_a():
    \"\"\"
    # A
    \"\"\"

def test_a_2():
    pass

def test_b():
    \"\"\"
    # B
    \"\"\"
"""

SECTION_C = """
def test_c():
    \"\"\"
    # C
    \"\"\"

@since(3, 13)
def test_c_2():
    pass
"""


def test_get_content_orders_sections_by_toc(tmp_path):
    toc = write_content(tmp_path, ['b', 'c', 'a'],
                        test_content=SECTION_A, test_content_py312=SECTION_C)

    result = get_content(folder=tmp_path, toc=toc)

    assert [e.name for e in result] == ['b', 'c', 'c_2', 'a', 'a_2']
    # The version of a versioned module is the default for its examples.
    assert [e.since for e in result] == [None, (3, 12), (3, 13), None, None]
    assert [e.show_badge for e in result] == [False, True, True, False, False]


@pytest.mark.parametrize('toc, message', [
    (['a', 'c'], "'b' exists but isn't listed"),
    (['a', 'b', 'c', 'd'], "'d' is listed but doesn't exist"),
    (['a', 'b', 'c', 'a'], "'a' is listed more than once"),
])
def test_get_content_rejects_toc_mismatch(tmp_path, toc, message):
    toc_path = write_content(tmp_path, toc,
                             test_content=SECTION_A, test_content_py312=SECTION_C)
    with pytest.raises(ContentError, match=message):
        get_content(folder=tmp_path, toc=toc_path)


def test_get_content_rejects_untitled_first_example(tmp_path):
    toc = write_content(tmp_path, ['a', 'b'], test_content=SECTION_A,
                        test_content_py312="def test_orphan():\n    pass\n")
    with pytest.raises(ContentError, match="'orphan' has no title"):
        get_content(folder=tmp_path, toc=toc)


@pytest.mark.skipif(sys.version_info < (required_python(ROOT / 'tests') or (3,)),
                    reason="Not all content modules parse on this Python")
def test_toc_matches_content():
    examples = get_content(folder=ROOT / 'tests', toc=ROOT / 'toc.toml')
    assert examples[0].name == 'simple'


def test_generate_needs_newest_python(monkeypatch, tmp_path):
    monkeypatch.setattr(main, 'required_python', lambda: (99, 0))
    output = tmp_path / 'index.html'

    result = CliRunner().invoke(main.main, ['generate', '-o', str(output)])

    assert result.exit_code == 1
    assert 'Generating the site needs Python 99.0+' in result.output
    assert not output.exists()
def func_to_ast(func):
    source = textwrap.dedent(inspect.getsource(func))
    return ast.parse(source).body[0], source
