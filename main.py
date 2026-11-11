import ast
import dataclasses
import datetime
import hashlib
import logging
import subprocess
import sys
from logging import getLogger
from collections import namedtuple
from pathlib import Path
from textwrap import dedent, indent

import jinja2
import sass
import click
import markdown
import markupsafe
import pygments
import pygments.formatters
import pygments.lexers


log = getLogger(__name__)

CONTENT_MODULE_PATH = Path("tests/test_content.py")

Flavor = namedtuple('Flavor', ('key', 'variable', 'label', 'name', 'selectable'))

#: The formatting styles shown on the page, in display order. Each example
#: in the content module assigns the code for a style to ``variable``.
#: Selectable styles can be toggled with the picker at the top of the page.
FLAVORS = (
    Flavor('percent', 'percent_result', '%', '%-formatting', True),
    Flavor('format', 'format_result', '.format()', '.format()', True),
    Flavor('fstring', 'fstring_result', 'f-string', 'f-strings', True),
    Flavor('tstring', 'tstring_result', 't-string', 't-strings', False),
)

FLAVOR_BY_VARIABLE = {flavor.variable: flavor for flavor in FLAVORS}

Section = namedtuple('Section', ('name', 'title', 'details', 'examples'))

Version = namedtuple('Version', ('revid', 'datetime'))


@dataclasses.dataclass(frozen=True)
class Example:
    name: str
    title: str = None
    details: str = None
    setup: str = ""
    #: Maps a flavor key (see ``FLAVORS``) to the code for that style.
    variants: dict = dataclasses.field(default_factory=dict)
    output: str = ""
    #: Minimum Python version as a tuple, e.g. ``(3, 8)``, or ``None``.
    since: tuple = None
    #: Whether the version badge should be rendered (see ``mark_badges``).
    show_badge: bool = False

    @property
    def has_selectable(self):
        return any(f.selectable and f.key in self.variants for f in FLAVORS)

    @property
    def since_label(self):
        if not self.since:
            return ""
        return "Python {}+".format(".".join(str(part) for part in self.since))

    def _replace(self, **changes):
        return dataclasses.replace(self, **changes)


def generate_version():
    revid = subprocess.check_output(
        ['git', 'rev-parse', 'HEAD']).decode('utf-8').rstrip()
    dt = datetime.datetime.now(datetime.timezone.utc)
    return Version(revid=revid, datetime=dt)


def compile_sass(source_path, target_path_pattern):
    # First generate the content from which we can generate the hashname
    log.info("Compiling SCSS.")
    output = sass.compile(
        filename=str(source_path),
        output_style='compressed')
    hash = hashlib.sha512(output.encode('utf-8')).hexdigest()[:8]
    target_path = str(target_path_pattern).format(hash)
    source_map_target_path = target_path + '.map'
    output = sass.compile(
        filename=str(source_path),
        output_style='compressed',
        source_map_filename=source_map_target_path)
    with open(target_path, 'w') as fp:
        fp.write(output[0])
    with open(source_map_target_path, 'w') as fp:
        fp.write(output[1])
    return Path(target_path)


def generate_css(base_folder, target_folder):
    log.info("Generating CSS.")
    file_mapping = {}
    target_folder = target_folder
    try:
        target_folder.mkdir(parents=True)
    except FileExistsError:
        pass

    pygments_css = base_folder / '_pygments.scss'
    with open(str(pygments_css), 'w') as fp:
        fp.write(pygments.formatters.HtmlFormatter().get_style_defs(
            '.highlight'))

    for file_ in base_folder.glob('*.scss'):
        if not file_.name.startswith('_'):
            target_path = target_folder / (file_.stem + '.{}.css')
            target_path = compile_sass(file_, target_path)
            file_mapping[file_.name] = target_path.name
    return file_mapping


def split_letters(value):
    return markupsafe.Markup('').join(
        markupsafe.Markup('<i>{}</i>').format(letter) for letter in value)


def highlight(value):
    return pygments.highlight(value, pygments.lexers.PythonLexer(),
                              pygments.formatters.HtmlFormatter())


def render_html(content):
    env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
    env.filters['markdown'] = markdown.markdown
    env.filters['lettering'] = split_letters
    env.filters['highlight'] = highlight
    tmpl = env.get_template('index.html')
    style_mapping = generate_css(Path('assets/sass'), Path('assets/css'))
    return tmpl.render(examples=list(content), styles=style_mapping,
                       flavors=FLAVORS, version=generate_version())


def generate_html(content, output_file):
    log.info("Rendering HTML.")
    html = render_html(content)
    with open(str(output_file), 'w', encoding='utf-8') as fp:
        fp.write(html)


def parse_docstring(docstring):
    if not docstring:
        return (None, None)
    lines = docstring.rstrip().split('\n')
    if len(lines) < 1:
        return (None, None)
    if lines[0].startswith('# '):
        return (lines[0][2:], '\n'.join(lines[2:]) or None)
    else:
        return (None, '\n'.join(lines) or None)


def source_of(source, node):
    """
    Return the code of ``node`` exactly as it was written in ``source``.

    ``ast.unparse`` can't be used here as it doesn't round-trip all syntax
    (e.g. ``f'{value=}'`` would become ``f'value={value!r}'``).
    """
    return dedent(ast.get_source_segment(source, node, padded=True)).strip()


def source_of_statements(source, nodes):
    """
    Return the source lines spanning all ``nodes``, including any comments
    in between.
    """
    lines = source.splitlines()[nodes[0].lineno - 1:nodes[-1].end_lineno]
    return dedent('\n'.join(lines)).strip()


def is_str_constant(node):
    return isinstance(node, ast.Constant) and isinstance(node.value, str)


def parse_since(node):
    """
    Return the version passed to a ``@since(3, 8)`` decorator, or ``None``.
    """
    for decorator in node.decorator_list:
        if (isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Name)
                and decorator.func.id == 'since'):
            return tuple(arg.value for arg in decorator.args)
    return None


def result_flavor(node):
    """
    Return the flavor if ``node`` assigns to one of the ``*_result``
    variables listed in ``FLAVORS``.
    """
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        if isinstance(target, ast.Name):
            return FLAVOR_BY_VARIABLE.get(target.id)
    return None


def parse_function(node, source):
    variants = {}
    output = None
    setup = []
    setup_done = False
    title, details = parse_docstring(ast.get_docstring(node, clean=True))
    name = node.name[5:] if node.name.startswith('test_') else node.name

    for n in node.body:
        # Ignore the docstring
        if isinstance(n, ast.Expr) and is_str_constant(n.value):
            continue
        flavor = result_flavor(n)
        if flavor:
            setup_done = True
            variants[flavor.key] = source_of(source, n.value)
        if (isinstance(n, ast.Assert)
                and isinstance(n.test, ast.Compare)
                and is_str_constant(n.test.comparators[-1])):
            setup_done = True
            output = n.test.comparators[-1].value
        if not setup_done:
            setup.append(n)

    return Example(
        name=name,
        title=title,
        details=details,
        setup=source_of_statements(source, setup) if setup else "",
        variants={f.key: variants[f.key] for f in FLAVORS if f.key in variants},
        output=output or "",
        since=parse_since(node),
    )


def parse_class(node, source):
    """
    parse_class parses the given node representing a test class for example
    test cases and puts everything into a Section object.
    """
    name = node.name[4:]
    title, details = parse_docstring(ast.get_docstring(node))
    examples = []

    for n in node.body:
        if isinstance(n, ast.FunctionDef) and n.name.startswith('test_'):
            example = parse_function(n, source)
            examples.append(example._replace(
                name='{}__{}'.format(name, example.name)))

    return Section(name, title, details, mark_badges(examples))


def mark_badges(items):
    """
    Decide which examples show their version badge: every titled example
    that has one, and a continuation only if its version differs from the
    example before it. This avoids repeating the same badge on every
    example of a section. Non-example items (sections) are passed through.
    """
    result = []
    previous = None
    for item in items:
        if not isinstance(item, Example):
            result.append(item)
            previous = None
            continue
        if item.title:
            previous = None
        show = bool(item.since) and item.since != previous
        result.append(item._replace(show_badge=show))
        previous = item.since
    return result


def get_content(filename=None):
    """
    get_content generates sections or examples out of the given file path.
    """
    log.info("Parsing content.")
    if filename is None:
        filename = CONTENT_MODULE_PATH
    with open(str(filename), encoding='utf-8') as fp:
        source = fp.read()
    module = ast.parse(source)
    items = []
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
            items.append(parse_function(node, source))
        if isinstance(node, ast.ClassDef) and node.name.startswith('Test'):
            items.append(parse_class(node, source))
    return mark_badges(items)


@click.group()
def main():
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format="%(levelname)-7s %(name)s: %(message)s")


@main.command()
@click.option('-o', '--output', default='index.html',
              help="Path to the output HTML file")
def generate(output):
    generate_html(get_content(), Path(output))
    log.info("Done.")


@main.command()
@click.option('-v', '--verbose', is_flag=True,
              help="Print function definitions")
def extract(verbose):
    cnt = 0
    for example in get_content():
        cnt += 1
        if verbose:
            print("Function: {}".format(example.name))
            if example.title:
                print("    Title:\n{}".format(indent(example.title, " " * 8)))
            if example.details:
                print("    Details:\n{}".format(indent(example.details, " " * 8)))
            if example.since:
                print("    Since: {}".format(example.since_label))
            print("    Example:")
            if example.setup:
                print("        Setup:\n{}".format(indent(example.setup, " " * 14)))
            for flavor in FLAVORS:
                if flavor.key in example.variants:
                    code = indent(example.variants[flavor.key], " " * 12).lstrip()
                    print("        {}: {}".format(flavor.label, code))
            print("        Output: {}".format(example.output))
            print()
    print("Extracted {} examples.".format(cnt))


if __name__ == "__main__":
    main()
