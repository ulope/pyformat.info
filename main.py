import ast
import dataclasses
import datetime
import hashlib
import logging
import re
import subprocess
import sys
import tomllib
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

#: Where the examples live. ``test_content.py`` must work on every supported
#: Python version, examples that need newer syntax live in
#: ``test_content_py3NN.py`` modules which need Python 3.NN.
CONTENT_DIR = Path("tests")
VERSIONED_MODULE_RE = re.compile(r"test_content_py3(\d+)\.py")

#: The order of the sections on the page.
TOC_PATH = Path("toc.toml")

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


class ContentError(click.ClickException):
    """The content modules and ``toc.toml`` don't fit together."""


def format_version(version):
    return ".".join(str(part) for part in version)


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
        return "Python {}+".format(format_version(self.since))

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


def parse_function(node, source, since=None):
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
        since=parse_since(node) or since,
    )


def parse_class(node, source, since=None):
    """
    parse_class parses the given node representing a test class for example
    test cases and puts everything into a Section object.
    """
    name = node.name[4:]
    title, details = parse_docstring(ast.get_docstring(node))
    examples = []

    for n in node.body:
        if isinstance(n, ast.FunctionDef) and n.name.startswith('test_'):
            example = parse_function(n, source, since)
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


def content_modules(folder=CONTENT_DIR):
    """
    Return ``(path, min_version)`` for every content module. ``min_version``
    is ``None`` for ``test_content.py`` and e.g. ``(3, 12)`` for
    ``test_content_py312.py``.
    """
    modules = [(folder / 'test_content.py', None)]
    for path in sorted(folder.glob('test_content_py3*.py')):
        match = VERSIONED_MODULE_RE.fullmatch(path.name)
        if match:
            modules.append((path, (3, int(match.group(1)))))
    return modules


def required_python(folder=CONTENT_DIR):
    """
    Return the Python version needed to parse all content modules, or
    ``None`` if every supported version can.
    """
    return max((v for _, v in content_modules(folder) if v), default=None)


def parse_module(filename, since=None):
    """
    Parse a content module into examples (and sections for test classes) in
    the order they are defined. ``since`` is the default minimum Python
    version for its examples.
    """
    with open(str(filename), encoding='utf-8') as fp:
        source = fp.read()
    module = ast.parse(source)
    items = []
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
            items.append(parse_function(node, source, since))
        if isinstance(node, ast.ClassDef) and node.name.startswith('Test'):
            items.append(parse_class(node, source, since))
    return items


def group_sections(items, origin):
    """
    Split the items of one module into sections: a titled example (or a
    test class) followed by the untitled examples that continue it. Returns
    a dict mapping the section id (the name of its first item) to its items.
    """
    sections = {}
    current = None
    for item in items:
        if isinstance(item, Section) or item.title:
            current = sections.setdefault(item.name, [])
        elif current is None:
            raise ContentError(
                "{}: example '{}' has no title, so it doesn't belong to a "
                "section. Give it a '# Title' or move it after the example "
                "it continues.".format(origin, item.name))
        current.append(item)
    return sections


def read_toc(path=TOC_PATH):
    with open(str(path), 'rb') as fp:
        return tomllib.load(fp)['sections']


def get_content(filename=None, folder=CONTENT_DIR, toc=TOC_PATH):
    """
    get_content parses the examples and returns them in page order.

    Without ``filename`` all content modules in ``folder`` are read and their
    sections are ordered as listed in ``toc``. With ``filename`` only that
    module is read and the examples keep their definition order.
    """
    log.info("Parsing content.")
    if filename is not None:
        return mark_badges(parse_module(filename))

    sections = {}
    for path, version in content_modules(folder):
        for name, items in group_sections(parse_module(path, version), path).items():
            if name in sections:
                raise ContentError(
                    "Section '{}' is defined more than once.".format(name))
            sections[name] = items

    order = read_toc(toc)
    problems = []
    for name in sorted({name for name in order if order.count(name) > 1}):
        problems.append("'{}' is listed more than once".format(name))
    for name in order:
        if name not in sections:
            problems.append("'{}' is listed but doesn't exist".format(name))
    for name in sections:
        if name not in order:
            problems.append("'{}' exists but isn't listed".format(name))
    if problems:
        raise ContentError("{} doesn't match the content: {}.".format(
            toc, "; ".join(problems)))

    return mark_badges([item for name in order for item in sections[name]])


def check_python_version():
    """
    Parsing all examples needs a Python version that knows all the syntax
    they use, see ``content_modules()``.
    """
    required = required_python()
    if required and sys.version_info < required:
        raise click.ClickException(
            "Generating the site needs Python {}+ because some examples use "
            "syntax older versions can't parse. This is Python {}.".format(
                format_version(required),
                format_version(sys.version_info[:3])))


def _requirement_help():
    required = required_python()
    if not required:
        return ""
    return " Needs Python {}+ to parse all examples.".format(
        format_version(required))


@click.group()
def main():
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format="%(levelname)-7s %(name)s: %(message)s")


@main.command(help="Generate the website." + _requirement_help())
@click.option('-o', '--output', default='index.html',
              help="Path to the output HTML file")
def generate(output):
    check_python_version()
    generate_html(get_content(), Path(output))
    log.info("Done.")


@main.command(help="List the parsed examples." + _requirement_help())
@click.option('-v', '--verbose', is_flag=True,
              help="Print function definitions")
def extract(verbose):
    check_python_version()
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
