import ast
import inspect

from pathlib import Path
from shutil import rmtree

import wrapt

from main import parse_docstring
from main import parse_function
from main import get_content
from main import split_letters
from main import generate_css


def test_split_letters():
    assert split_letters('a bc') == '<i>a</i><i> </i><i>b</i><i>c</i>'


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


def dummy_long():
    """
    # Title

    Blah
    """

    x = {'a': 1}

    old_result = "%(a)s" % x
    new_result = "{x.a}".format(x=x)

    assert new_result == "1"
    assert old_result == new_result


def test_parse_function_complete():
    example = parse_function(func_to_ast(dummy_long))

    assert example.name == 'dummy_long'
    assert example.title == "Title"
    assert example.details == "Blah"
    assert example.setup == "x = {'a': 1}"
    assert example.old == "'%(a)s' % x"
    assert example.new == "'{x.a}'.format(x=x)"
    assert example.output == "1"


def dummy_minimal():
    new_result = "{}".format(1)

    assert new_result == "1"  # output


def test_parse_function_minimal():
    example = parse_function(func_to_ast(dummy_minimal))

    assert example.name == 'dummy_minimal'
    assert example.title is None
    assert example.details is None
    assert example.setup == ""
    assert example.old == ""
    assert example.new == "'{}'.format(1)"
    assert example.output == "1"


def dummy_empty():
    pass


def test_parse_function_empty():
    example = parse_function(func_to_ast(dummy_empty))

    assert example.name == 'dummy_empty'
    assert example.title is None
    assert example.details is None
    assert example.setup == "pass"
    assert example.old == ""
    assert example.new == ""
    assert example.output == ""


@wrapt.decorator
def dummy_decorator(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)


@dummy_decorator
def dummy_decorated():
    pass


def test_parse_decorated():
    example = parse_function(func_to_ast(dummy_decorated))
    assert example.name == 'dummy_decorated'
    assert example.setup == 'pass'


def test_get_content(tmpdir):
    testfile = tmpdir.join('test_content.py')
    testfile.write('''
def test_something():
    new_result = '{}'.format('hello')
    assert new_result == 'hello'

def unknown():
    pass
    ''')

    result = list(get_content(filename=str(testfile)))
    assert len(result) == 1



def func_to_ast(func):
    return ast.parse(inspect.getsource(func)).body[0]
